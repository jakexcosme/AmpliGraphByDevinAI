# Copyright 2019-2023 The AmpliGraph Authors. All Rights Reserved.
#
# This file is Licensed under the Apache License, Version 2.0.
# A copy of the Licence is available in LICENCE, or at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
import pytest
import numpy as np
import tempfile
import os
from ampligraph.datasets.datasets import _clean_data, load_mapper_from_json


def test_clean_data_memory_optimization():
    """Test _clean_data memory usage with large datasets"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    large_data = {
        'train': np.array([['entity_{}'.format(i), 'relation', 'entity_{}'.format(i+1)] 
                          for i in range(50000)]),
        'valid': np.array([['entity_1', 'relation', 'entity_2']]),
        'test': np.array([['entity_1', 'relation', 'entity_2']])
    }
    
    clean_data = _clean_data(large_data)
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    assert memory_increase < 500 * 1024 * 1024
    assert len(clean_data['train']) == 50000


def test_clean_data_edge_case_empty_strings():
    """Test _clean_data with empty string entities/relations"""
    X = {
        'train': np.array([['', 'relation', 'entity'], ['entity', '', 'entity2'], ['entity', 'relation', '']]),
        'valid': np.array([['entity', 'relation', 'entity2']]),
        'test': np.array([['entity', 'relation', 'entity2']])
    }
    
    clean_X = _clean_data(X)
    assert len(clean_X['train']) == 0
    assert len(clean_X['valid']) == 1
    assert len(clean_X['test']) == 1


def test_clean_data_whitespace_handling():
    """Test _clean_data with whitespace-only entities"""
    X = {
        'train': np.array([['  ', 'relation', 'entity'], ['entity', 'relation', '\t\n']]),
        'valid': np.array([['entity', 'relation', 'entity2']]),
        'test': np.array([['entity', 'relation', 'entity2']])
    }
    
    clean_X = _clean_data(X)
    assert len(clean_X['valid']) == 1
    assert len(clean_X['test']) == 1


def test_clean_data_numeric_entities():
    """Test _clean_data with numeric entity identifiers"""
    X = {
        'train': np.array([['123', 'relation', '456'], ['789', 'relation2', '101112']]),
        'valid': np.array([['123', 'relation', '456']]),
        'test': np.array([['123', 'relation', '456']])
    }
    
    clean_X = _clean_data(X)
    assert len(clean_X['train']) == 2
    assert len(clean_X['valid']) == 1
    assert len(clean_X['test']) == 1
    np.testing.assert_array_equal(clean_X['train'][0], ['123', 'relation', '456'])


def test_clean_data_very_long_entity_names():
    """Test _clean_data with very long entity names"""
    long_entity = 'entity_' + 'x' * 1000
    X = {
        'train': np.array([[long_entity, 'relation', 'entity2']]),
        'valid': np.array([[long_entity, 'relation', 'entity2']]),
        'test': np.array([[long_entity, 'relation', 'entity2']])
    }
    
    clean_X = _clean_data(X)
    assert len(clean_X['train']) == 1
    assert len(clean_X['valid']) == 1
    assert len(clean_X['test']) == 1
    assert clean_X['train'][0][0] == long_entity


def test_load_mapper_from_json_file_not_found():
    """Test load_mapper_from_json with non-existent file"""
    with pytest.raises(FileNotFoundError):
        load_mapper_from_json('/nonexistent/path/mapper.json')


def test_load_mapper_from_json_invalid_json():
    """Test load_mapper_from_json with invalid JSON"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('invalid json content {')
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            load_mapper_from_json(temp_path)
    finally:
        os.unlink(temp_path)


def test_load_mapper_from_json_valid():
    """Test load_mapper_from_json with valid JSON"""
    mapper_data = {
        'entity1': 0,
        'entity2': 1,
        'relation1': 0,
        'relation2': 1
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        import json
        json.dump(mapper_data, f)
        temp_path = f.name
    
    try:
        loaded_mapper = load_mapper_from_json(temp_path)
        assert loaded_mapper == mapper_data
    finally:
        os.unlink(temp_path)


def test_clean_data_cross_dataset_consistency():
    """Test _clean_data maintains consistency across train/valid/test splits"""
    X = {
        'train': np.array([['a', 'r1', 'b'], ['c', 'r2', 'd'], ['e', 'r3', 'f']]),
        'valid': np.array([['a', 'r1', 'b'], ['g', 'r4', 'h']]),  # g,h not in train
        'test': np.array([['c', 'r2', 'd'], ['i', 'r5', 'j']])    # i,j not in train
    }
    
    clean_X, valid_idx, test_idx = _clean_data(X, return_idx=True)
    
    assert len(clean_X['valid']) == 1  # Only a,r1,b should remain
    assert len(clean_X['test']) == 1   # Only c,r2,d should remain
    
    np.testing.assert_array_equal(clean_X['valid'][0], ['a', 'r1', 'b'])
    np.testing.assert_array_equal(clean_X['test'][0], ['c', 'r2', 'd'])


def test_clean_data_relation_consistency():
    """Test _clean_data handles relation consistency"""
    X = {
        'train': np.array([['a', 'r1', 'b'], ['c', 'r2', 'd']]),
        'valid': np.array([['a', 'r3', 'b']]),  # r3 not in train
        'test': np.array([['c', 'r2', 'd']])    # r2 in train
    }
    
    clean_X = _clean_data(X)
    
    assert len(clean_X['train']) == 2
    assert len(clean_X['test']) == 1


def test_clean_data_performance_large_validation():
    """Test _clean_data performance with large validation/test sets"""
    import time
    
    train_data = np.array([['entity_{}'.format(i), 'relation', 'entity_{}'.format(i+1)] 
                          for i in range(1000)])
    valid_data = np.array([['entity_{}'.format(i), 'relation', 'entity_{}'.format(i+1)] 
                          for i in range(10000)])  # Much larger than train
    
    X = {
        'train': train_data,
        'valid': valid_data,
        'test': np.array([['entity_1', 'relation', 'entity_2']])
    }
    
    start_time = time.time()
    clean_X = _clean_data(X)
    processing_time = time.time() - start_time
    
    assert processing_time < 30.0
    assert len(clean_X['train']) == 1000
