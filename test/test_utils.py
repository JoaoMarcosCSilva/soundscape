import utils
import tensorflow as tf
from jax import numpy as jnp
import jax

import pytest


# Functions used in test_parallel_map since it's not possible to use lambdas.
def inc_fn(x):
    return x + 1


def sqr_fn(x):
    return x * x


@pytest.mark.parametrize(
    "fn,x",
    [
        (inc_fn, [1, 2, 3, 4, 5]),
        (inc_fn, []),
        (sqr_fn, [-1, 0, 1, 2, 3]),
    ],
)
def test_parallel_map(fn, x):
    y_pred = utils.parallel_map(fn, x, use_tqdm=False)
    y_true = list(map(fn, x))
    assert y_pred == y_true


@pytest.mark.parametrize(
    "array",
    [
        [1, 2, 3, 4, 5],
        [1],
        {"a": [1, 2], "b": [3, 4], "c": [[5], [6]], "d": "string"},
        "string",
    ],
)
def test_tf_jax(array):
    if type(array) == list:
        x_tf = tf.constant(array)
        x_jax = jnp.array(array)
    else:
        x_tf = jax.tree_util.tree_map(tf.constant, array)
        x_jax = jax.tree_util.tree_map(
            lambda x: jnp.array(x) if type(x) != str else x, array
        )

    y_jax = utils.tf2jax(x_tf)
    y_tf = utils.jax2tf(x_jax)

    assert jnp.all(y_jax == x_jax)
    assert jnp.all(utils.tf2jax(y_tf) == x_jax)


@pytest.mark.parametrize(
    "tensor_length, time, expected",
    [
        (60, 0, 0),
        (60, 5, 5),
        (60, 61, 61),
        (60, -1, -1),
        (128, 30, 64),
        (128, 15, 32),
        (10, 12, 2),
    ],
)
def test_time2pos(tensor_length, time, expected):
    result = utils.time2pos(tensor_length, time)
    assert result == expected


def assert_dicts_equal(d1, d2):
    assert d1.keys() == d2.keys()
    for key in d1.keys():
        if type(d1[key]) == dict:
            assert_dicts_equal(d1[key], d2[key])
        else:
            assert d1[key] == d2[key]


@pytest.mark.parametrize(
    "d",
    [
        {"a": 1, "b": 2},
        {"a": 3, "b": 4},
        {"a": {"c": 5, "d": 6}, "b": 2},
    ],
)
def test_hash_dict(d):
    d_hashed = utils.hash_dict(d)
    assert_dicts_equal(d, d_hashed)
    assert hash(d_hashed) is not None
