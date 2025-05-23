class EvaluationMetrics:
    @staticmethod
    def get_precision(actual, pred, start_entities):
        actual_set = set(a for a in actual if a not in start_entities)
        pred_set = set(p for p in pred if p not in start_entities)

        true_positives = len(actual_set.intersection(pred_set))
        false_positives = len(pred_set - actual_set)

        if true_positives + false_positives == 0:
            return 0.0
        return true_positives / (true_positives + false_positives)

    @staticmethod
    def get_recall(actual, pred, start_entities):
        actual_set = set(a for a in actual if a not in start_entities)
        pred_set = set(p for p in pred if p not in start_entities)

        true_positives = len(actual_set.intersection(pred_set))
        false_negatives = len(actual_set - pred_set)

        if true_positives + false_negatives == 0:
            return 0.0
        return true_positives / (true_positives + false_negatives)

    @staticmethod
    def get_f1_score(actual, pred, start_entities):
        precision = EvaluationMetrics.get_precision(actual, pred, start_entities)
        recall = EvaluationMetrics.get_recall(actual, pred, start_entities)

        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
