import math
import torch
import torch.nn as nn
import torch.nn.functional as F

 
def compute_sdm_per(scores, pid, logit_scale, epsilon=1e-8):
    """
    Similarity Distribution Matching
    """
    batch_size = scores.shape[0]
    pid = pid.reshape((batch_size, 1)) # make sure pid size is [batch_size, 1]
    pid_dist = pid - pid.t()
    labels = (pid_dist == 0).float()

    t2i_cosine_theta = scores
    i2t_cosine_theta = t2i_cosine_theta.t()

    text_proj_image = logit_scale * t2i_cosine_theta
    image_proj_text = logit_scale * i2t_cosine_theta

    # normalize the true matching distribution
    labels_distribute = labels / labels.sum(dim=1)

    i2t_pred = F.softmax(image_proj_text, dim=1)
    i2t_loss = i2t_pred * (F.log_softmax(image_proj_text, dim=1) - torch.log(labels_distribute + epsilon))
    t2i_pred = F.softmax(text_proj_image, dim=1)
    t2i_loss = t2i_pred * (F.log_softmax(text_proj_image, dim=1) - torch.log(labels_distribute + epsilon))

    loss = torch.sum(i2t_loss, dim=1) + torch.sum(t2i_loss, dim=1)

    return loss

def compute_TRL_per(scores, pid, margin = 0.2, tau=0.02):       
    batch_size = scores.shape[0]
    pid = pid.reshape((batch_size, 1)) # make sure pid size is [batch_size, 1]
    pid_dist = pid - pid.t()
    labels = (pid_dist == 0).float().to(scores.device)
    mask = 1 - labels

    alpha_1 =((scores/tau).exp()* labels / ((scores/tau).exp()* labels).sum(dim=1, keepdim=True)).detach()
    alpha_2 = ((scores.t()/tau).exp()* labels / ((scores.t()/tau).exp()* labels).sum(dim=1, keepdim=True)).detach()

    pos_1 = (alpha_1 * scores).sum(1)
    pos_2 = (alpha_2 * scores.t()).sum(1)

    neg_1 = (mask*scores).max(1)[0]
    neg_2 = (mask*scores.t()).max(1)[0]

    cost_1 = (margin + neg_1 - pos_1).clamp(min=0)
    cost_2 = (margin + neg_2 - pos_2).clamp(min=0)
    return cost_1 + cost_2

 
def compute_InfoNCE_per(scores, logit_scale):
    
    # cosine similarity as logits
    logits_per_image = logit_scale * scores
    logits_per_text = logits_per_image.t()

    p1 = F.softmax(logits_per_image, dim=1)
    p2 = F.softmax(logits_per_text, dim=1)

    loss = (- p1.diag().log() - p2.diag().log())/2    
    return loss

def compute_TAL_per(scores, pid, tau, margin):       
    batch_size = scores.shape[0]
    pid = pid.reshape((batch_size, 1)) # make sure pid size is [batch_size, 1]
    pid_dist = pid - pid.t()
    labels = (pid_dist == 0).float().to(scores.device)
    mask = 1 - labels

    alpha_i2t =((scores/tau).exp()* labels / ((scores/tau).exp()* labels).sum(dim=1, keepdim=True)).detach()
    alpha_t2i = ((scores.t()/tau).exp()* labels / ((scores.t()/tau).exp()* labels).sum(dim=1, keepdim=True)).detach()

    loss = (-  (alpha_i2t*scores).sum(1) + tau * ((scores / tau).exp() * mask).sum(1).clamp(max=10e35).log() + margin).clamp(min=0)  \
        +  (-  (alpha_t2i*scores.t()).sum(1) + tau * ((scores.t() / tau).exp() * mask).sum(1).clamp(max=10e35).log() + margin).clamp(min=0)
    
    return loss 

def compute_rbs(i_feats, t_feats, i_tse_f, t_tse_f, pid, label_hat=None, tau=0.02, margin=0.1, loss_type='TAL', logit_scale=50):

    loss_bgm, _ = compute_per_loss(i_feats, t_feats, pid, tau, margin, loss_type, logit_scale)
    loss_tse, _ = compute_per_loss(i_tse_f, t_tse_f, pid, tau, margin, loss_type, logit_scale)

    loss_bgm = (label_hat*loss_bgm).sum()
    loss_tse = (label_hat*loss_tse).sum()
    
    if loss_type in ['TAL','TRL']:
        return loss_bgm, loss_tse
    else:
        return loss_bgm/label_hat.sum(), loss_tse/label_hat.sum() # mean

def compute_per_loss(image_features, text_features, pid, tau=0.02, margin=0.2, loss_type='TAL', logit_scale=50):
    
    # # normalized features
    image_norm = image_features / image_features.norm(dim=-1, keepdim=True)
    text_norm = text_features / text_features.norm(dim=-1, keepdim=True)
    scores = text_norm @ image_norm.t()

    if 'TAL' in loss_type:
        per_loss = compute_TAL_per(scores, pid, tau, margin=margin)
    elif 'TRL' in loss_type:
        per_loss = compute_TRL_per(scores, pid, tau=tau, margin=margin)
    elif 'InfoNCE' in loss_type:
        per_loss = compute_InfoNCE_per(scores, logit_scale)
    elif 'SDM' in loss_type:
        per_loss = compute_sdm_per(scores, pid, logit_scale)
    else:
        exit()

    return per_loss, scores.diag()


def compute_agree_scores(i_g, t_g, i_l, t_l):
    """
    GLAW agreement scores: how well image and text features match.
    Higher = more confident the pair is a match.
    """
    sim_g = (i_g * t_g).sum(dim=1)
    sim_l = (i_l * t_l).sum(dim=1)
    agree = torch.sigmoid((sim_g + sim_l) / 2.0)
    return agree


def compute_glaw_loss(i_feats, t_feats, i_tse_f, t_tse_f, pid, tau=0.015, margin=0.1, logit_scale=50):
    """
    GLAW: Agreement-weighted Dual TAL loss.
    Global branch (i_feats/t_feats) + Local branch (i_tse_f/t_tse_f),
    each computed with TAL loss, then weighted by agreement scores.
    """
    i_g = F.normalize(i_feats, p=2, dim=-1)
    t_g = F.normalize(t_feats, p=2, dim=-1)
    i_l = F.normalize(i_tse_f, p=2, dim=-1)
    t_l = F.normalize(t_tse_f, p=2, dim=-1)

    agree = compute_agree_scores(i_g, t_g, i_l, t_l).detach()

    loss_bgm, _ = compute_per_loss(i_feats, t_feats, pid, tau, margin, 'TAL', logit_scale)
    loss_tse, _ = compute_per_loss(i_tse_f, t_tse_f, pid, tau, margin, 'TAL', logit_scale)

    return (agree * loss_bgm).sum() + (agree * loss_tse).sum()


def compute_fdr_loss(i_feats, t_feats, i_tse_f, t_tse_f, weight=1.0, noise_std=0.1):
    """
    Feature Denoising Regularization (FDR)
    """
    i_noise = i_feats + torch.randn_like(i_feats) * noise_std
    t_noise = t_feats + torch.randn_like(t_feats) * noise_std
    i_g = F.normalize(i_feats, p=2, dim=-1)
    t_g = F.normalize(t_feats, p=2, dim=-1)
    i_n = F.normalize(i_noise, p=2, dim=-1)
    t_n = F.normalize(t_noise, p=2, dim=-1)
    i_l = F.normalize(i_tse_f, p=2, dim=-1)
    t_l = F.normalize(t_tse_f, p=2, dim=-1)
    i_ln = F.normalize(i_tse_f + torch.randn_like(i_tse_f) * noise_std, p=2, dim=-1)
    t_ln = F.normalize(t_tse_f + torch.randn_like(t_tse_f) * noise_std, p=2, dim=-1)
    loss_global = F.mse_loss((i_n * t_n).sum(dim=1), (i_g * t_g).sum(dim=1))
    loss_local = F.mse_loss((i_ln * t_ln).sum(dim=1), (i_l * t_l).sum(dim=1))
    return (loss_global + loss_local) * weight * 0.5


def compute_centroid_loss(i_feats, t_feats, pid, agree, centroids, momentum=0.99, weight=0.5):
    """
    EMA centroid pull: maintain per-ID EMA centroids, pull features toward them
    weighted by agreement score. Centroid updated from clean samples (agree > 0.5).
    """
    i_feats = F.normalize(i_feats, p=2, dim=-1)
    t_feats = F.normalize(t_feats, p=2, dim=-1)
    all_feats = torch.cat([i_feats, t_feats], dim=0)
    all_pid = torch.cat([pid, pid], dim=0)
    all_agree = torch.cat([agree, agree], dim=0)
    unique_pids = torch.unique(all_pid)
    loss = 0.0
    for p in unique_pids:
        p_item = p.item()
        pid_mask = (all_pid == p)
        mask_clean = pid_mask & (all_agree > 0.5)
        if mask_clean.sum() == 0:
            mask_clean = pid_mask & (all_agree > 0.3)
        if mask_clean.sum() == 0:
            continue
        curr_mean = all_feats[mask_clean].mean(dim=0)
        if p_item not in centroids:
            centroids[p_item] = curr_mean
        else:
            centroids[p_item] = momentum * centroids[p_item] + (1 - momentum) * curr_mean
        sim = (all_feats[pid_mask] * centroids[p_item].detach()).sum(dim=1)
        loss = loss + ((1 - sim) * all_agree[pid_mask]).sum()
    return loss * weight / max(len(unique_pids), 1)



