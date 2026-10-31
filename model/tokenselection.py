import torch
import torch.nn as nn
import torch.nn.functional as F
 
def l2norm(X, dim, eps=1e-8):
    """L2-normalize columns of X
    """
    norm = torch.pow(X, 2).sum(dim=dim, keepdim=True).sqrt() + eps
    X = torch.div(X, norm)
    return X


def maxk_pool1d_var(x, dim, k, lengths):
    """https://github.com/woodfrog/vse_infty, thanks!"""
    results = list()
    lengths = list(lengths.cpu().numpy())
    lengths = [int(x) for x in lengths]
    for idx, length in enumerate(lengths):
        k = min(k, length)
        max_k_i = maxk(x[idx, :length, :], dim - 1, k).mean(dim - 1)
        results.append(max_k_i)
    results = torch.stack(results, dim=0)
    return results

def maxk_pool1d(x, dim, k):
    max_k = maxk(x, dim, k)
    return max_k.mean(dim)

def maxk(x, dim, k):
    index = x.topk(k, dim=dim)[1]
    return x.gather(dim, index)


class MLP(nn.Module):
    """ Very simple multi-layer perceptron (also called FFN) from https://github.com/woodfrog/vse_infty, thanks!"""

    def __init__(self, input_dim, hidden_dim, output_dim, num_layers):
        super().__init__()
        self.output_dim = output_dim
        self.num_layers = num_layers
        h = [hidden_dim] * (num_layers - 1)
        self.layers = nn.ModuleList(nn.Linear(n, k) for n, k in zip([input_dim] + h, h + [output_dim]))
        self.bns = nn.ModuleList(nn.BatchNorm1d(k) for k in h + [output_dim])

    def forward(self, x):
        B, N, D = x.size()
        x = x.reshape(B * N, D)
        for i, (bn, layer) in enumerate(zip(self.bns, self.layers)):
            x = F.relu(bn(layer(x))) if i < self.num_layers - 1 else layer(x)
        x = x.view(B, N, self.output_dim)
        return x
 
class TexualEmbeddingLayer(nn.Module):
    def __init__(self, input_dim=512, embed_dim=1024,ratio=0.3):
        super(TexualEmbeddingLayer, self).__init__()
        self.embed_dim= embed_dim
        self.linear = nn.Linear(input_dim, embed_dim)
        self.mlp = MLP(input_dim, embed_dim // 2, embed_dim, 2)
        self.ratio = ratio

    def forward(self, features, text, atten, image_features=None, image_atten=None):
        mask =  ((text != 0) + 0)
        lengths = mask.sum(1).view(-1) - 2
        k = int((atten.size(1)-2)*self.ratio)
        bs = features.size(0)
        atten[torch.arange(bs), :, text.argmax(dim=-1)] = -1
        atten[torch.arange(bs), :, 0] = -1
        atten = atten[torch.arange(bs), text.argmax(dim=-1), :]
        atten = atten * mask
        
        atten_topK = atten.topk(dim=-1,k = k)[1].unsqueeze(-1).expand(bs,k,features.size(2))
        features = torch.gather(input=features,dim=1,index=atten_topK)
        features = l2norm(features, dim=-1)

        lengths = torch.Tensor([lengths[i] if lengths[i] < k else k for i in range(bs)])
        
        cap_emb = self.linear(features.half())
        features = self.mlp(features) + cap_emb
        features = maxk_pool1d_var(features, 1, 1, lengths.to(cap_emb.device))
        
        return features.float()

class VisualEmbeddingLayer(nn.Module):
    def __init__(self, input_dim=512, embed_dim=1024,ratio=0.3):
        super(VisualEmbeddingLayer, self).__init__()
        self.embed_dim= embed_dim
        self.linear = nn.Linear(input_dim, embed_dim)
        self.ratio = ratio
        self.fc = nn.Linear(input_dim, embed_dim)
        self.mlp = MLP(input_dim, embed_dim // 2, embed_dim, 2)
    
    def forward(self, base_features, atten, text_features=None, text_atten=None, text_ids=None):
        k = int((atten.size(1)-1)*self.ratio)
        
        bs = base_features.size(0)
        atten[torch.arange(bs), :, 0] = -1
        atten_topK = atten[:,0].topk(dim=-1,k = k)[1]
        
        atten_topK = atten_topK.unsqueeze(-1).expand(bs, k, base_features.size(2))
        base_features = torch.gather(input=base_features,dim=1,index=atten_topK)
        base_features = l2norm(base_features, dim=-1) 
        base_features = base_features.half()
        feat_lengths = torch.zeros(base_features.size(0)).to(base_features.device).half()
        feat_lengths[:] = base_features.size(1)
        
        features = self.fc(base_features)
        features = self.mlp(base_features) + features 
        features = maxk_pool1d_var(features, 1, 1, feat_lengths)

        return features.float()


class CMATS_VisualEmbeddingLayer(nn.Module):
    def __init__(self, input_dim=512, embed_dim=1024, ratio=0.3, cm_alpha=0.5):
        super().__init__()
        self.embed_dim = embed_dim
        self.ratio = ratio
        self.cm_alpha = cm_alpha
        self.v_proj = nn.Linear(input_dim, input_dim)
        self.t_proj = nn.Linear(input_dim, input_dim)
        self.fc = nn.Linear(input_dim, embed_dim)
        self.mlp = MLP(input_dim, embed_dim // 2, embed_dim, 2)

    def forward(self, base_features, atten, text_features=None, text_atten=None, text_ids=None):
        k = int((atten.size(1)-1)*self.ratio)
        bs = base_features.size(0)

        attn_cls = atten[:, 0, 1:].clone()
        vis_patches = base_features[:, 1:, :]

        if text_features is not None and text_atten is not None and text_ids is not None:
            eos_idx = text_ids.argmax(dim=-1)
            text_attn = text_atten[torch.arange(bs), eos_idx, :].clone()
            text_attn[:, 0] = -1
            text_attn[torch.arange(bs), eos_idx] = -1
            mask = (text_ids != 0).float()
            text_attn = text_attn * mask

            v_proj = self.v_proj(vis_patches)
            t_proj = self.t_proj(text_features)
            cross_sim = torch.bmm(v_proj, t_proj.transpose(1, 2)) / (base_features.size(-1) ** 0.5)
            cross_attn = F.softmax(cross_sim, dim=-1)

            text_imp = text_attn.unsqueeze(1)
            vis_cross = (cross_attn * text_imp).sum(dim=-1)

            imp = attn_cls + self.cm_alpha * vis_cross
        else:
            imp = attn_cls

        _, indices = imp.topk(k=k, dim=-1)
        indices = indices.unsqueeze(-1).expand(bs, k, base_features.size(2))
        sel = torch.gather(base_features, dim=1, index=indices)
        sel = l2norm(sel, dim=-1).half()
        lengths = torch.full((bs,), k, device=sel.device, dtype=torch.half)

        feat = self.fc(sel)
        feat = self.mlp(sel) + feat
        feat = maxk_pool1d_var(feat, 1, 1, lengths)

        return feat.float()


class CMATS_TextualEmbeddingLayer(nn.Module):
    def __init__(self, input_dim=512, embed_dim=1024, ratio=0.3, cm_alpha=0.5):
        super().__init__()
        self.embed_dim = embed_dim
        self.ratio = ratio
        self.cm_alpha = cm_alpha
        self.v_proj = nn.Linear(input_dim, input_dim)
        self.t_proj = nn.Linear(input_dim, input_dim)
        self.linear = nn.Linear(input_dim, embed_dim)
        self.mlp = MLP(input_dim, embed_dim // 2, embed_dim, 2)

    def forward(self, features, text, atten, image_features=None, image_atten=None):
        mask = (text != 0).float()
        lengths = mask.sum(1).view(-1) - 2
        k = int((atten.size(1)-2)*self.ratio)
        bs = features.size(0)

        eos_idx = text.argmax(dim=-1)
        text_attn = atten[torch.arange(bs), eos_idx, :].clone()
        text_attn[:, 0] = -1
        text_attn[torch.arange(bs), eos_idx] = -1
        text_attn = text_attn * mask

        if image_features is not None and image_atten is not None:
            vis_attn = image_atten[:, 0, 1:].clone()
            vis_patches = image_features[:, 1:, :]

            v_proj = self.v_proj(vis_patches)
            t_proj = self.t_proj(features)
            cross_sim = torch.bmm(t_proj, v_proj.transpose(1, 2)) / (features.size(-1) ** 0.5)
            cross_attn = F.softmax(cross_sim, dim=-1)

            vis_imp = vis_attn.unsqueeze(1)
            text_cross = (cross_attn * vis_imp).sum(dim=-1)

            imp = text_attn + self.cm_alpha * text_cross
        else:
            imp = text_attn

        imp = imp * mask
        _, indices = imp.topk(k=k, dim=-1)
        indices = indices.unsqueeze(-1).expand(bs, k, features.size(2))
        sel = torch.gather(features, dim=1, index=indices)
        sel = l2norm(sel, dim=-1)

        lengths = torch.Tensor([min(lengths[i].item(), k) for i in range(bs)])

        cap_emb = self.linear(sel.half())
        sel = self.mlp(sel) + cap_emb
        sel = maxk_pool1d_var(sel, 1, 1, lengths.to(cap_emb.device))

        return sel.float()
