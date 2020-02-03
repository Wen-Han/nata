from random import randint

import attr
import pytest
import numpy as np

from nata.containers.grid import GridDataset
from nata.containers.grid import BaseGrid
from nata.containers.axes import IterationAxis
from nata.containers.axes import TimeAxis
from nata.containers.axes import GridAxis
from nata.containers.axes import DataStock


@pytest.fixture(name="remove_GridDataset_backends")
def _removeBackends():
    # setup code
    previous_backends = GridDataset._backends.copy()
    GridDataset._backends.clear()
    assert len(GridDataset._backends) == 0

    yield

    # teardown code
    GridDataset._backends = previous_backends
    assert len(GridDataset._backends) != 0


@pytest.fixture(name="GridBackend")
def _return_custom_grid():
    class CustomGrid(BaseGrid):
        @property
        def name(self):
            return "custom_grid"

        @property
        def iteration(self):
            if self._value:
                return self._value
            return 0

        @property
        def time_step(self):
            if self._value:
                return self._value * 10.0
            return 0.0

        @property
        def time_unit(self):
            return "time unit"

        @property
        def axes_names(self):
            return ["x1"]

        @property
        def axes_labels(self):
            return ["x_1"]

        @property
        def axes_units(self):
            return ["x1 units"]

        @property
        def axes_min(self):
            return [-5.0]

        @property
        def axes_max(self):
            return [5.0]

        @property
        def dataset(self):
            return np.arange(10.0, dtype=float)

        @property
        def dataset_name(self):
            return "dataset short"

        @property
        def dataset_label(self):
            return "dataset long"

        @property
        def dataset_unit(self):
            return "dataset unit"

        @property
        def location(self):
            return None

        @property
        def shape(self):
            return self.dataset.shape

        @property
        def dim(self):
            return len(self.shape)

        @property
        def dtype(self):
            return self.dataset.dtype

        @staticmethod
        def is_valid_backend(s):
            pass

        def __init__(self, value=None):
            self._value = value

    return CustomGrid


def test_GridDataset_init(GridBackend):
    grid = GridDataset(GridBackend())

    assert grid.backend == "custom_grid"
    assert grid.location is None
    assert grid.name == "dataset short"
    assert grid.label == "dataset long"
    assert grid.unit == "dataset unit"
    assert grid._step is None

    for attr, instance, value in (
        ("iteration", IterationAxis, None),
        ("time", TimeAxis, None),
        ("_data", DataStock, None),
        ("grid_shape", tuple, (10,)),
        ("grid_dim", int, 1),
        ("grid_dtype", np.dtype, np.float),
        ("axes", list, None),
        ("x1", GridAxis, None),
    ):
        assert hasattr(grid, attr)
        assert isinstance(getattr(grid, attr), instance)
        if value:
            assert getattr(grid, attr) == value


def test_DummyGridBackend(GridBackend):
    backend = GridBackend(10)
    assert backend.iteration == 10
    assert backend.time_step == 100.0


@pytest.mark.parametrize("l", range(10))
def test_GridDataset_len(l):
    ds = GridDataset.__new__(GridDataset)
    ds.iteration = range(l)
    assert len(ds) == l


def test_GridDataset_append(GridBackend):
    ds = GridDataset(GridBackend(1))
    other = GridDataset(GridBackend(2))

    ds.append(other)

    assert len(ds) == 2
    assert len(ds.iteration) == 2
    assert len(ds.time) == 2
    assert len(ds.x1) == 2
    assert len(ds.axes) == 1
    assert len(ds._data._mapping) == 2


def test_GridDataset_data_getter():
    ds = GridDataset.__new__(GridDataset)
    ds._data = [i for i in range(10)]
    ds._step = None
    np.testing.assert_array_equal(ds.data, range(10))
    ds._step = 5
    np.testing.assert_array_equal(ds.data, [5])


def test_GridDataset_data_getter():
    ds = GridDataset.__new__(GridDataset)
    ds._step = None
    ds._data = [i for i in range(10)]
    np.testing.assert_array_equal(ds.data, range(10))

    new_data = [i * 2 for i in range(10)]
    ds.data = new_data
    np.testing.assert_array_equal(ds._data, new_data)

    ds._step = 5
    ds.data = -5
    new_data[5] = -5
    np.testing.assert_array_equal(ds._data, new_data)


def test_GridDataset_copy():
    ds = GridDataset.__new__(GridDataset)

    for f in attr.fields(GridDataset):
        if f.eq:
            setattr(ds, f.name, randint(0, 10))

    new = ds.copy()

    assert ds is not new
    assert ds == new


def test_GridDataset_iter():
    ds = GridDataset.__new__(GridDataset)
    ds.iteration = {0: 1, 10: 2, 20: 3}

    for s, step in zip(ds, (0, 10, 20)):
        assert s is ds
        assert s._step == step

    for (return_s, s), step in zip(ds.iter(), (0, 10, 20)):
        assert s is ds
        assert s._step == step
        assert return_s == step

    for (return_s, s), step in zip(ds.iter(with_iteration=True), (0, 10, 20)):
        assert s is ds
        assert s._step == step
        assert return_s == step

    for s, step in zip(ds.iter(with_iteration=False), (0, 10, 20)):
        assert s is ds
        assert s._step == step


def test_GridDataset_from_array():
    ds = GridDataset.from_array(np.arange(10))
    np.testing.assert_array_equal(ds.data, np.arange(10).reshape((1, 10)))

    ds = GridDataset.from_array(
        np.arange(10).reshape((2, 5)), time=[0, 1], iteration=[0, 1]
    )
    np.testing.assert_array_equal(ds.data, np.arange(10).reshape((2, 5)))