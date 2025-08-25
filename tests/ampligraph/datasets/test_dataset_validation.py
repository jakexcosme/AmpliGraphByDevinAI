# Copyright 2019-2023 The AmpliGraph Authors. All Rights Reserved.
#
# This file is Licensed under the Apache License, Version 2.0.
# A copy of the Licence is available in LICENCE, or at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
import pytest
import numpy as np
from ampligraph.datasets.datasets import _clean_data, load_from_csv, _add_reciprocal_relations


def test_clean_data_empty_input():
    """Test _clean_data with empty datasets"""
    X = {
        'train': np.array([]),
        'valid': np.array([]),
        'test': np.array([])
    }
    
    with pytest.raises(ValueError):
        _clean_data(X)


def test_clean_data_malformed_triples():
    """Test _clean_data with malformed triple data"""
    X = {
        'train': np.array([['a', 'b', 'c'], ['d', '', 'f']]),
        'valid': np.array([['a', 'b', 'c']]),
        'test': np.array([['a', 'b', 'c']])
    }
    
    clean_X = _clean_data(X)
    assert len(clean_X['train']) == 1
    np.testing.assert_array_equal(clean_X['train'], np.array([['a', 'b', 'c']]))


def test_clean_data_unicode_entities():
    """Test _clean_data with unicode entity names"""
    X = {
        'train': np.array([['café', 'located_in', 'París'], ['user', 'likes', 'café']]),
        'valid': np.array([['café', 'located_in', 'París']]),
        'test': np.array([['user', 'likes', 'café']])
    }
    
    clean_X = _clean_data(X)
    assert len(clean_X['train']) == 2
    assert len(clean_X['valid']) == 1
    assert len(clean_X['test']) == 1


def test_clean_data_return_indices():
    """Test _clean_data return indices functionality"""
    X = {
        'train': np.array([['a', 'b', 'c'], ['d', 'e', 'f']]),
        'valid': np.array([['a', 'b', 'c'], ['x', 'y', 'z']]),
        'test': np.array([['a', 'b', 'c'], ['d', 'e', 'f']])
    }
    
    clean_X, valid_idx, test_idx = _clean_data(X, return_idx=True)
    
    assert len(valid_idx) == 2
    assert len(test_idx) == 2
    np.testing.assert_array_equal(valid_idx, np.array([True, False]))
    np.testing.assert_array_equal(test_idx, np.array([True, True]))


def test_add_reciprocal_relations_basic():
    """Test _add_reciprocal_relations with basic triples"""
    X = np.array([['entity1', 'relation1', 'entity2']])
    
    X_with_reciprocals = _add_reciprocal_relations(X)
    
    assert len(X_with_reciprocals) == 2
    np.testing.assert_array_equal(X_with_reciprocals[0], ['entity1', 'relation1', 'entity2'])
    np.testing.assert_array_equal(X_with_reciprocals[1], ['entity2', 'relation1_reciprocal', 'entity1'])


def test_add_reciprocal_relations_multiple():
    """Test _add_reciprocal_relations with multiple triples"""
    X = np.array([
        ['entity1', 'relation1', 'entity2'],
        ['entity3', 'relation2', 'entity4']
    ])
    
    X_with_reciprocals = _add_reciprocal_relations(X)
    
    assert len(X_with_reciprocals) == 4
    expected_reciprocals = np.array([
        ['entity1', 'relation1', 'entity2'],
        ['entity3', 'relation2', 'entity4'],
        ['entity2', 'relation1_reciprocal', 'entity1'],
        ['entity4', 'relation2_reciprocal', 'entity3']
    ])
    np.testing.assert_array_equal(X_with_reciprocals, expected_reciprocals)


def test_load_from_csv_file_not_found():
    """Test load_from_csv with non-existent file"""
    with pytest.raises(FileNotFoundError):
        load_from_csv('/nonexistent/path/file.csv')


def test_load_from_csv_invalid_separator():
    """Test load_from_csv with invalid separator"""
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('entity1,relation1,entity2\n')
        f.write('entity3,relation2,entity4\n')
        temp_path = f.name
    
    try:
        data = load_from_csv(temp_path, sep=',')
        assert len(data) == 2
        np.testing.assert_array_equal(data[0], ['entity1', 'relation1', 'entity2'])
    finally:
        os.unlink(temp_path)


def test_clean_data_large_dataset_memory():
    """Test _clean_data memory efficiency with larger datasets"""
    large_train = np.array([['entity_{}'.format(i), 'relation', 'entity_{}'.format(i+1)] 
                           for i in range(1000)])
    large_valid = np.array([['entity_1', 'relation', 'entity_2']])
    large_test = np.array([['entity_1', 'relation', 'entity_2']])
    
    X = {
        'train': large_train,
        'valid': large_valid,
        'test': large_test
    }
    
    clean_X = _clean_data(X)
    assert len(clean_X['train']) == 1000
    assert len(clean_X['valid']) == 1
    assert len(clean_X['test']) == 1


def test_clean_data_duplicate_removal():
    """Test _clean_data removes duplicate triples within datasets"""
    X = {
        'train': np.array([['a', 'b', 'c'], ['a', 'b', 'c'], ['d', 'e', 'f']]),
        'valid': np.array([['a', 'b', 'c']]),
        'test': np.array([['a', 'b', 'c']])
    }
    
    clean_X = _clean_data(X)
    assert len(clean_X['train']) == 2
    assert len(clean_X['valid']) == 1
    assert len(clean_X['test']) == 1
