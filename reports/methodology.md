# Research Methodology: Decoding Strategies in Indic Neural Machine Translation

## 1. Theoretical Framework of Sequence Decoding

In autoregressive Neural Machine Translation (NMT), given a source sequence $\mathbf{x} = (x_1, x_2, \dots, x_S)$, the model parameterized by $\theta$ defines a conditional probability distribution over the target sequence $\mathbf{y} = (y_1, y_2, \dots, y_T)$:

$$P(\mathbf{y} \mid \mathbf{x}; \theta) = \prod_{t=1}^{T} P(y_t \mid y_{<t}, \mathbf{x}; \theta)$$

The theoretical inference objective is Maximum A Posteriori (MAP) decoding:

$$\mathbf{y}^* = \arg\max_{\mathbf{y} \in \mathcal{Y}} \sum_{t=1}^{T} \log P(y_t \mid y_{<t}, \mathbf{x}; \theta)$$

Because the search space $\mathcal{Y} = \mathcal{V}^T$ scales exponentially with output length $T$ and vocabulary size $|\mathcal{V}|$ (where $|\mathcal{V}| \approx 122,706$ in IndicTrans2), exact search via dynamic programming is intractable. Practical systems therefore rely on heuristic search algorithms.

---

## 2. Algorithmic Formulations

### 2.1 Greedy Search Decoding
Greedy Search makes locally optimal decisions at each generation step $t$, choosing the token with maximum conditional probability:

$$y_t = \arg\max_{w \in \mathcal{V}} P(w \mid y_{<t}, \mathbf{x})$$

- **Time Complexity:** $\mathcal{O}(T \cdot |\mathcal{V}|)$
- **Space Complexity:** $\mathcal{O}(T)$
- **Characteristics:** Highly efficient on CPU hardware. However, it cannot correct suboptimal early decisions—if an incorrect word is chosen early, subsequent generations compound the error.

### 2.2 Beam Search Decoding
Beam Search maintains a set $\mathcal{B}_t$ of the top-$k$ most promising partial hypotheses of length $t$:

$$\mathcal{B}_t = \text{arg top-}k \left\{ \sum_{i=1}^{t} \log P(y_i \mid y_{<i}, \mathbf{x}) \;\middle|\; (y_1, \dots, y_{t-1}) \in \mathcal{B}_{t-1}, \, y_t \in \mathcal{V} \right\}$$

- **Time Complexity:** $\mathcal{O}(k \cdot T \cdot |\mathcal{V}|)$
- **Space Complexity:** $\mathcal{O}(k \cdot T)$
- **Length Normalization:** Without length penalties, Beam Search systematically favors shorter sequences due to cumulative negative log-probabilities. Length penalty $\alpha$ mitigates this:
  $$\text{Score}(\mathbf{y}) = \frac{\sum_{t=1}^{T} \log P(y_t \mid y_{<t}, \mathbf{x})}{\left(\frac{5 + T}{6}\right)^\alpha}$$

---

## 3. The Search Error vs Model Error Paradox

A widespread assumption in NLP is that increasing beam width $k$ monotonically improves translation quality. However, empirical studies (e.g., Koehn & Knowles, 2017) reveal that:
1. **Search Errors:** When the model assigns high probability to a good translation, but the search algorithm fails to find it.
2. **Model Errors:** When the model assigns higher probability to an unnatural, repetitive, or empty translation.

In Indic-to-English translation, excessively large beam widths ($k \ge 8$) can degrade BLEU by uncovering degenerate high-probability hypotheses that do not reflect human linguistic adequacy.

---

## 4. Indic Language Linguistic Challenges
1. **Morphological Richness and Agglutination:** Tamil is an agglutinative Dravidian language where nominal case markers, verbal conjugations, and postpositions attach directly to root stems (e.g., *செயற்கை நுண்ணறிவு* = "artificial intelligence", *சென்னையிலிருந்து* = "from Chennai").
2. **Subword Segmentation:** SentencePiece decomposes agglutinated tokens into fine-grained subword pieces. Errors in subword boundary prediction in greedy decoding can cause translation hallucination, which Beam Search partially mitigates by evaluating multiple prefix paths.

---

## 5. Economic Cost Modeling for Production Deployment

To translate algorithmic differences into industrial metrics, we model the total compute cost $C$ for translating $N$ sentences at throughput $R_k$ (sentences/sec):

$$t_{\text{compute}} = \frac{N}{R_k}$$

For a cloud instance billed at $P_{\text{hourly}}$ USD/hour:

$$C_{\text{cloud}} = \left(\frac{t_{\text{compute}}}{3600}\right) \times P_{\text{hourly}}$$

For local on-premise CPU servers with power consumption $W$ Watts and electricity tariff $E_{\text{kWh}}$:

$$C_{\text{local}} = \left(\frac{W}{1000}\right) \times \left(\frac{t_{\text{compute}}}{3600}\right) \times E_{\text{kWh}}$$

The Cost-Quality Frontier $\mathcal{F}$ enables researchers and system architects to identify whether a +0.5 BLEU gain justifies a 2.5x to 3.5x increase in operational expenditure.
