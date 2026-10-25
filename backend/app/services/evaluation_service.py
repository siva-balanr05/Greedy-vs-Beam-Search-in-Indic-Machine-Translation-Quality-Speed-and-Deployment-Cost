from typing import List, Dict, Any, Optional
import sacrebleu

class EvaluationService:
    @staticmethod
    def compute_sentence_metrics(
        hypothesis: str,
        reference: Optional[str]
    ) -> Dict[str, Any]:
        """
        Computes sentence-level BLEU and chrF when reference is provided.
        Includes a scientific note explaining sentence-level n-gram sparsity.
        """
        if not reference or not reference.strip() or not hypothesis or not hypothesis.strip():
            return {
                "sentence_bleu": None,
                "sentence_chrf": None,
                "note": "Reference translation not provided or empty."
            }
            
        hyp = hypothesis.strip()
        ref = reference.strip()
        
        try:
            # sacrebleu sentence_bleu requires hypothesis string and list of reference strings
            bleu = sacrebleu.sentence_bleu(hyp, [ref])
            chrf = sacrebleu.sentence_chrf(hyp, [ref])
            
            return {
                "sentence_bleu": round(bleu.score, 2),
                "sentence_chrf": round(chrf.score, 2),
                "note": (
                    "Sentence-level BLEU is sensitive to zero higher-order n-gram matches in short sentences. "
                    "chrF (character n-gram F-score) is generally more informative at the sentence level."
                )
            }
        except Exception as e:
            return {
                "sentence_bleu": None,
                "sentence_chrf": None,
                "error": str(e)
            }

    @staticmethod
    def compute_corpus_metrics(
        hypotheses: List[str],
        references: List[str]
    ) -> Dict[str, Any]:
        """
        Computes corpus-level SacreBLEU and chrF scores across a parallel evaluation set.
        """
        valid_pairs = [
            (h.strip(), r.strip())
            for h, r in zip(hypotheses, references)
            if r and r.strip()
        ]
        
        if not valid_pairs:
            return {
                "corpus_bleu": None,
                "corpus_chrf": None,
                "evaluated_samples": 0,
                "note": "No valid reference pairs available for corpus evaluation."
            }
            
        hyps = [p[0] for p in valid_pairs]
        refs = [[p[1] for p in valid_pairs]]  # sacrebleu expects list of reference streams
        
        try:
            bleu = sacrebleu.corpus_bleu(hyps, refs)
            chrf = sacrebleu.corpus_chrf(hyps, refs)
            
            return {
                "corpus_bleu": round(bleu.score, 2),
                "corpus_chrf": round(chrf.score, 2),
                "evaluated_samples": len(valid_pairs),
                "sys_len": bleu.sys_len,
                "ref_len": bleu.ref_len,
                "brevity_penalty": round(bleu.bp, 4)
            }
        except Exception as e:
            return {
                "corpus_bleu": None,
                "corpus_chrf": None,
                "evaluated_samples": len(valid_pairs),
                "error": str(e)
            }

evaluation_service = EvaluationService()
