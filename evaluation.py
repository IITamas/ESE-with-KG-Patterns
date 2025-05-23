class EvaluationMetrics:
    """Calculate evaluation metrics for entity set expansion."""

    @staticmethod
    def get_precision(actual, pred, start_entities):
        """
        Calculate precision of the expanded entity set.

        Precision = TP / (TP + FP)
        where:
        - TP = entities correctly identified (in both predicted and actual sets)
        - FP = entities incorrectly identified (in predicted but not in actual set)
        """
        # Remove start entities from both sets
        actual = [a for a in actual if a not in start_entities]
        pred = [p for p in pred if p not in start_entities]

        # Calculate true positives and false positives
        tp = sum(1 for p in pred if p in actual)
        fp = sum(1 for p in pred if p not in actual)

        # Avoid division by zero
        if tp + fp == 0:
            return 0.0

        return tp / (tp + fp)

    @staticmethod
    def get_recall(actual, pred, start_entities):
        """
        Calculate recall (coverage) of the expanded entity set.

        Recall = TP / (TP + FN)
        where:
        - TP = entities correctly identified (in both predicted and actual sets)
        - FN = entities missed (in actual but not in predicted set)
        """
        # Remove start entities from both sets
        actual = [a for a in actual if a not in start_entities]
        pred = [p for p in pred if p not in start_entities]

        # Calculate true positives and false negatives
        tp = sum(1 for a in actual if a in pred)
        fn = sum(1 for a in actual if a not in pred)

        # Avoid division by zero
        if tp + fn == 0:
            return 0.0

        return tp / (tp + fn)

    @staticmethod
    def get_f1_score(actual, pred, start_entities):
        """
        Calculate F1 score, the harmonic mean of precision and recall.

        F1 = 2 * (precision * recall) / (precision + recall)
        """
        precision = EvaluationMetrics.get_precision(actual, pred, start_entities)
        recall = EvaluationMetrics.get_recall(actual, pred, start_entities)

        # Avoid division by zero
        if precision + recall == 0:
            return 0.0

        return 2 * (precision * recall) / (precision + recall)
