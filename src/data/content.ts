export const SITE = {
  repo: 'https://github.com/bili186/GLAW',
  title: 'GLAW — text-based person search',
  description:
    'A CLIP ViT-B/16 two-branch model for text-based person search, where a global branch and a token-selected local branch are weighted per pair by their image-text agreement score.',
  paperTitle:
    'Global-Local Agreement-Weighted Dual-Feature Learning for Text-Based Person Search',
  authors: 'Zhe Xu, Haoning Deng, Zhengye Zhang, Zhijie Yao, Kun Zhang',
  corresponding: 'Kun Zhang',
};

export const queries = [
  {
    tag: 'Query A',
    text: 'The man with the dark hair is wearing a red overcoat and a pair of gray trousers.And he is carrying a black backpack.',
  },
  {
    tag: 'Query B',
    text: 'Back of a female walker covering hair with red scarf taking a big laggage.Red coins and with Black pants.She also wears a pair of boots.',
  },
];

export const metrics = [
  { dataset: 'CUHK-PEDES', r1: '74.27', r5: '89.80', r10: '94.15', map: '66.36', minp: '50.06' },
  { dataset: 'ICFG-PEDES', r1: '65.82', r5: '81.24', r10: '86.77', map: '39.22', minp: '7.66' },
  { dataset: 'RSTPReid', r1: '65.60', r5: '83.80', r10: '90.30', map: '50.89', minp: '28.13' },
];

export const mechanisms = [
  {
    name: 'CMATS',
    sub: 'cross-modal attention token selection',
    body: 'Visual patches and text tokens are scored by bidirectional cross-modal attention, and the <b>top 30% of each modality</b> survive into the local branch. Selection is a ranking rather than a threshold, so it holds whatever the length of the description.',
  },
  {
    name: 'GLAW loss',
    sub: 'agreement-weighted dual TAL',
    body: 'A global branch and the token-selected local branch are optimised together. Each branch carries a weight from the sigmoid of its own image–text agreement score, so a reliable pair drives the gradient while an unreliable one steps back — <b>the trade-off is per pair, not a fixed hyperparameter</b>.',
  },
  {
    name: 'FDR',
    sub: 'feature denoising regularisation',
    body: 'Gaussian noise (σ = 0.1) is injected into the bypass features during training, and the cosine similarities of the noisy and clean features are matched with an MSE term — <b>flattening the similarity landscape</b> around each identity.',
  },
  {
    name: 'Centroid loss',
    sub: 'EMA identity centres',
    body: 'Class centroids, updated by exponential moving average from clean samples only, pull each feature toward its identity centre, weighted by the same agreement score.',
  },
];
