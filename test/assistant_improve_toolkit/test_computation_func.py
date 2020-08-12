import sys
sys.path.insert(0, './src')
from assistant_improve_toolkit import intersection


def test_intersection():
    list1 = ['node_1', 'node_2']
    list2 = ['node_1', 'node_2', 'node_3']

    overlap = intersection(list1, list2)

    assert overlap == ['node_1', 'node_2']
