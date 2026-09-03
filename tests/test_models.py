import numpy as np
from beod.models import _evaluate


def test_evaluate_reports_rare_event_metrics():
    y=np.array([0]*95+[1]*5)
    p=np.concatenate([np.linspace(.001,.2,95),np.linspace(.8,.99,5)])
    m=_evaluate(y,p)
    assert m['auc'] > 0.9
    assert m['pr_auc'] > 0.5
    assert m['top_5pct_lift'] > 1
    assert m['brier_baseline'] > 0
    assert m['calibration_slope'] is not None
