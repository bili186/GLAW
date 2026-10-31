from model import objectives
import numpy as np
from .tokenselection import CMATS_VisualEmbeddingLayer, CMATS_TextualEmbeddingLayer
from .clip_model import build_CLIP_from_openai_pretrained, convert_weights
import torch
import torch.nn as nn
import torch.nn.functional as F


class RDE(nn.Module):
    def __init__(self, args, num_classes=11003):
        super().__init__()
        self.args = args
        self.num_classes = num_classes

        self.base_model, base_cfg = build_CLIP_from_openai_pretrained(args.pretrain_choice, args.img_size, args.stride_size)
        self.embed_dim = base_cfg['embed_dim']

        self.logit_scale = torch.ones([]) * (1 / args.temperature)

        self.visul_emb_layer = CMATS_VisualEmbeddingLayer(ratio=args.select_ratio, cm_alpha=args.cm_alpha)
        self.texual_emb_layer = CMATS_TextualEmbeddingLayer(ratio=args.select_ratio, cm_alpha=args.cm_alpha)

        self.centroids = {}

    def encode_image(self, image):
        x, _ = self.base_model.encode_image(image)
        return x[:, 0, :].float()

    def encode_text(self, text):
        x, _ = self.base_model.encode_text(text.long())
        return x[torch.arange(x.shape[0]), text.argmax(dim=-1)].float()

    def encode_image_tse(self, image):
        x, atten_i = self.base_model.encode_image(image)
        i_tse_f = self.visul_emb_layer(x, atten_i)
        return i_tse_f.float()

    def encode_text_tse(self, text):
        x, atten_t = self.base_model.encode_text(text.long())
        t_tse_f = self.texual_emb_layer(x, text, atten_t)
        return t_tse_f.float()

    def forward(self, batch):
        images = batch['images']
        caption_ids = batch['caption_ids']
        pids = batch['pids']
        image_feats, atten_i, text_feats, atten_t = self.base_model(images, caption_ids)

        i_feats = image_feats[:, 0, :].float()
        t_feats = text_feats[torch.arange(text_feats.shape[0]), caption_ids.argmax(dim=-1)].float()

        i_tse_f = self.visul_emb_layer(image_feats, atten_i, text_features=text_feats, text_atten=atten_t, text_ids=caption_ids)
        t_tse_f = self.texual_emb_layer(text_feats, caption_ids, atten_t, image_features=image_feats, image_atten=atten_i)

        if self.training:
            ns = getattr(self.args, 'noise_std', 0.1)
            i_feats = i_feats + torch.randn_like(i_feats) * ns
            t_feats = t_feats + torch.randn_like(t_feats) * ns
            i_tse_f = i_tse_f + torch.randn_like(i_tse_f) * ns
            t_tse_f = t_tse_f + torch.randn_like(t_tse_f) * ns

        i_gn = F.normalize(i_feats, p=2, dim=-1)
        t_gn = F.normalize(t_feats, p=2, dim=-1)
        i_ln = F.normalize(i_tse_f, p=2, dim=-1)
        t_ln = F.normalize(t_tse_f, p=2, dim=-1)

        agree = objectives.compute_agree_scores(i_gn, t_gn, i_ln, t_ln)

        loss_glaw = objectives.compute_glaw_loss(i_feats, t_feats, i_tse_f, t_tse_f, pids, tau=self.args.tau, margin=self.args.margin, logit_scale=self.logit_scale)
        loss_fdr = objectives.compute_fdr_loss(i_feats, t_feats, i_tse_f, t_tse_f, weight=self.args.fdr_weight)
        loss_centroid = objectives.compute_centroid_loss(i_feats, t_feats, pids, agree, self.centroids,
            momentum=self.args.centroid_momentum, weight=self.args.centroid_weight)

        loss = loss_glaw + loss_fdr + loss_centroid

        i_feats_norm = F.normalize(i_feats, p=2, dim=-1)
        t_feats_norm = F.normalize(t_feats, p=2, dim=-1)
        scores = torch.matmul(i_feats_norm, t_feats_norm.t())

        ret = {
            'loss': loss,
            'scores': scores,
            'temperature': 1 / self.logit_scale,
        }
        return ret


def build_model(args, num_classes=11003):
    model = RDE(args, num_classes)
    convert_weights(model)
    return model
