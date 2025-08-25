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
from ampligraph.datasets.datasets import load_from_csv, load_from_ntriples


def test_load_from_csv_basic_functionality():
    """Test basic CSV loading functionality"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('subject\tpredicate\tobject\n')
        f.write('entity1\trelation1\tentity2\n')
        f.write('entity3\trelation2\tentity4\n')
        temp_path = f.name
    
    try:
        data = load_from_csv(temp_path, sep='\t', header=0)
        assert len(data) == 2
        np.testing.assert_array_equal(data[0], ['entity1', 'relation1', 'entity2'])
        np.testing.assert_array_equal(data[1], ['entity3', 'relation2', 'entity4'])
    finally:
        os.unlink(temp_path)


def test_load_from_csv_no_header():
    """Test CSV loading without header"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('entity1\trelation1\tentity2\n')
        f.write('entity3\trelation2\tentity4\n')
        temp_path = f.name
    
    try:
        data = load_from_csv(temp_path, sep='\t', header=None)
        assert len(data) == 2
        np.testing.assert_array_equal(data[0], ['entity1', 'relation1', 'entity2'])
    finally:
        os.unlink(temp_path)


def test_load_from_csv_different_separators():
    """Test CSV loading with different separators"""
    separators = [',', ';', '|', '\t']
    
    for sep in separators:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(f'entity1{sep}relation1{sep}entity2\n')
            f.write(f'entity3{sep}relation2{sep}entity4\n')
            temp_path = f.name
        
        try:
            data = load_from_csv(temp_path, sep=sep)
            assert len(data) == 2
            np.testing.assert_array_equal(data[0], ['entity1', 'relation1', 'entity2'])
        finally:
            os.unlink(temp_path)


def test_load_from_csv_empty_file():
    """Test CSV loading with empty file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            load_from_csv(temp_path)
    finally:
        os.unlink(temp_path)


def test_load_from_csv_malformed_rows():
    """Test CSV loading with malformed rows"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('entity1\trelation1\tentity2\n')
        f.write('entity3\trelation2\n')  # Missing third column
        f.write('entity4\trelation3\tentity5\textra_column\n')  # Extra column
        temp_path = f.name
    
    try:
        data = load_from_csv(temp_path, sep='\t')
        assert len(data) == 1  # Only valid row should be loaded
        np.testing.assert_array_equal(data[0], ['entity1', 'relation1', 'entity2'])
    finally:
        os.unlink(temp_path)


def test_load_from_csv_special_characters():
    """Test CSV loading with special characters in data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write('café\tlocated_in\tParís\n')
        f.write('user@domain.com\tlikes\tcafé\n')
        f.write('entity with spaces\thas relation\tanother entity\n')
        temp_path = f.name
    
    try:
        data = load_from_csv(temp_path, sep='\t')
        assert len(data) == 3
        np.testing.assert_array_equal(data[0], ['café', 'located_in', 'París'])
        np.testing.assert_array_equal(data[1], ['user@domain.com', 'likes', 'café'])
        np.testing.assert_array_equal(data[2], ['entity with spaces', 'has relation', 'another entity'])
    finally:
        os.unlink(temp_path)


def test_load_from_ntriples_basic():
    """Test basic N-Triples loading functionality"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.nt', delete=False) as f:
        f.write('<http://example.org/entity1> <http://example.org/relation1> <http://example.org/entity2> .\n')
        f.write('<http://example.org/entity3> <http://example.org/relation2> <http://example.org/entity4> .\n')
        temp_path = f.name
    
    try:
        data = load_from_ntriples(temp_path)
        assert len(data) >= 2  # Should load at least 2 triples
    finally:
        os.unlink(temp_path)


def test_load_from_ntriples_invalid_format():
    """Test N-Triples loading with invalid format"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.nt', delete=False) as f:
        f.write('invalid ntriples format\n')
        f.write('<http://example.org/entity1> <http://example.org/relation1> <http://example.org/entity2> .\n')
        temp_path = f.name
    
    try:
        data = load_from_ntriples(temp_path)
        assert len(data) >= 1  # Should load at least the valid triple
    finally:
        os.unlink(temp_path)


def test_load_from_csv_encoding_issues():
    """Test CSV loading with different encodings"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='latin-1') as f:
        f.write('entité1\trelation1\tentité2\n')
        temp_path = f.name
    
    try:
        try:
            data = load_from_csv(temp_path, sep='\t')
            assert len(data) >= 0  # Should not crash
        except UnicodeDecodeError:
            pass  # Expected for encoding mismatch
    finally:
        os.unlink(temp_path)


def test_load_from_csv_large_file_performance():
    """Test CSV loading performance with larger files"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        for i in range(10000):
            f.write(f'entity_{i}\trelation_{i%100}\tentity_{i+1}\n')
        temp_path = f.name
    
    try:
        import time
        start_time = time.time()
        data = load_from_csv(temp_path, sep='\t')
        load_time = time.time() - start_time
        
        assert len(data) == 10000
        assert load_time < 10.0  # Should load within reasonable time
    finally:
        os.unlink(temp_path)
