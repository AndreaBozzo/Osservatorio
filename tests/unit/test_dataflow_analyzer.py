"""
Unit tests for dataflow analyzer module.
"""

import pytest
import json
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from src.analyzers.dataflow_analyzer import IstatDataflowAnalyzer


class TestIstatDataflowAnalyzer:
    """Test ISTAT dataflow analyzer."""
    
    def test_init_creates_analyzer(self):
        """Test analyzer initialization."""
        analyzer = IstatDataflowAnalyzer()
        
        assert analyzer.base_url == "http://sdmx.istat.it/SDMXWS/rest/"
        assert analyzer.session is not None
        assert 'popolazione' in analyzer.category_keywords
        assert 'economia' in analyzer.category_keywords
        assert analyzer.category_keywords['popolazione']['priority'] == 10
        assert analyzer.category_keywords['economia']['priority'] == 9
    
    def test_category_keywords_structure(self):
        """Test category keywords are properly structured."""
        analyzer = IstatDataflowAnalyzer()
        
        for category, config in analyzer.category_keywords.items():
            assert 'keywords' in config
            assert 'priority' in config
            assert isinstance(config['keywords'], list)
            assert isinstance(config['priority'], int)
            assert len(config['keywords']) > 0
            assert config['priority'] > 0
    
    def test_extract_dataflow_info_with_namespaces(self):
        """Test extraction of dataflow info with SDMX namespaces."""
        analyzer = IstatDataflowAnalyzer()
        
        xml_content = '''
        <structure:Dataflow xmlns:structure="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
                           xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"
                           id="101_12" version="1.0">
            <common:Name xml:lang="it">Popolazione residente</common:Name>
            <common:Name xml:lang="en">Resident population</common:Name>
            <common:Description xml:lang="it">Dati sulla popolazione</common:Description>
        </structure:Dataflow>
        '''
        
        root = ET.fromstring(xml_content)
        namespaces = {
            'str': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure',
            'com': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common'
        }
        
        result = analyzer._extract_dataflow_info(root, namespaces)
        
        assert result is not None
        assert result['id'] == '101_12'
        assert result['name_it'] == 'Popolazione residente'
        assert result['name_en'] == 'Resident population'
        assert result['description'] == 'Dati sulla popolazione'
        assert result['display_name'] == 'Popolazione residente'
    
    def test_extract_dataflow_info_without_namespaces(self):
        """Test extraction of dataflow info without namespaces."""
        analyzer = IstatDataflowAnalyzer()
        
        xml_content = '''
        <Dataflow id="163_156" version="1.0">
            <Name lang="it">PIL regionale</Name>
            <Name lang="en">Regional GDP</Name>
            <Description lang="it">Prodotto interno lordo</Description>
        </Dataflow>
        '''
        
        root = ET.fromstring(xml_content)
        result = analyzer._extract_dataflow_info(root, {})
        
        assert result is not None
        assert result['id'] == '163_156'
        assert result['name_it'] == 'PIL regionale'
        assert result['name_en'] == 'Regional GDP'
        assert result['description'] == 'Prodotto interno lordo'
    
    def test_categorize_dataflows(self):
        """Test dataflow categorization."""
        analyzer = IstatDataflowAnalyzer()
        
        dataflows = [
            {
                'id': '101_12',
                'display_name': 'Popolazione residente',
                'description': 'Dati demografici popolazione'
            },
            {
                'id': '163_156',
                'display_name': 'PIL regionale',
                'description': 'Prodotto interno lordo economia'
            },
            {
                'id': '999_999',
                'display_name': 'Dataset sconosciuto',
                'description': 'Descrizione generica'
            }
        ]
        
        result = analyzer._categorize_dataflows(dataflows)
        
        # Check categorization
        assert len(result['popolazione']) == 1
        assert result['popolazione'][0]['id'] == '101_12'
        assert result['popolazione'][0]['category'] == 'popolazione'
        assert result['popolazione'][0]['relevance_score'] > 0
        
        assert len(result['economia']) == 1
        assert result['economia'][0]['id'] == '163_156'
        assert result['economia'][0]['category'] == 'economia'
        
        assert len(result['altri']) == 1
        assert result['altri'][0]['id'] == '999_999'
        assert result['altri'][0]['category'] == 'altri'
    
    def test_calculate_priority(self):
        """Test priority calculation."""
        analyzer = IstatDataflowAnalyzer()
        
        dataflow = {
            'relevance_score': 10,
            'tests': {
                'data_access': {'size_bytes': 5 * 1024 * 1024},  # 5MB
                'observations_count': 2000
            }
        }
        
        priority = analyzer._calculate_priority(dataflow)
        
        # Priority should be base score + size bonus + observation bonus
        assert priority > 10  # Should be higher than base relevance_score
        assert isinstance(priority, (int, float))
    
    def test_suggest_tableau_connection(self):
        """Test Tableau connection suggestion."""
        analyzer = IstatDataflowAnalyzer()
        
        # Large dataset
        large_dataflow = {
            'tests': {'data_access': {'size_bytes': 60 * 1024 * 1024}}  # 60MB
        }
        assert analyzer._suggest_tableau_connection(large_dataflow) == "bigquery_extract"
        
        # Medium dataset
        medium_dataflow = {
            'tests': {'data_access': {'size_bytes': 10 * 1024 * 1024}}  # 10MB
        }
        assert analyzer._suggest_tableau_connection(medium_dataflow) == "google_sheets_import"
        
        # Small dataset
        small_dataflow = {
            'tests': {'data_access': {'size_bytes': 1 * 1024 * 1024}}  # 1MB
        }
        assert analyzer._suggest_tableau_connection(small_dataflow) == "direct_connection"
    
    def test_suggest_refresh_frequency(self):
        """Test refresh frequency suggestion."""
        analyzer = IstatDataflowAnalyzer()
        
        assert analyzer._suggest_refresh_frequency('popolazione') == 'monthly'
        assert analyzer._suggest_refresh_frequency('economia') == 'quarterly'
        assert analyzer._suggest_refresh_frequency('lavoro') == 'monthly'
        assert analyzer._suggest_refresh_frequency('territorio') == 'yearly'
        assert analyzer._suggest_refresh_frequency('istruzione') == 'yearly'
        assert analyzer._suggest_refresh_frequency('salute') == 'quarterly'
        assert analyzer._suggest_refresh_frequency('unknown') == 'quarterly'
    
    @patch('builtins.open', new_callable=mock_open, read_data='sample xml content')
    @patch('xml.etree.ElementTree.parse')
    def test_parse_dataflow_xml_success(self, mock_parse, mock_file):
        """Test successful XML parsing."""
        analyzer = IstatDataflowAnalyzer()
        
        # Mock XML tree
        mock_tree = Mock()
        mock_root = Mock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree
        
        # Mock dataflow elements
        mock_dataflow = Mock()
        mock_dataflow.get.return_value = '101_12'
        mock_root.findall.return_value = [mock_dataflow]
        
        # Mock extraction method
        with patch.object(analyzer, '_extract_dataflow_info', return_value={
            'id': '101_12',
            'display_name': 'Test Dataflow',
            'description': 'Test description'
        }):
            with patch.object(analyzer, '_categorize_dataflows', return_value={
                'popolazione': [{'id': '101_12'}]
            }):
                result = analyzer.parse_dataflow_xml('test.xml')
                
                assert result is not None
                assert 'popolazione' in result
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_parse_dataflow_xml_file_not_found(self, mock_file):
        """Test XML parsing with missing file."""
        analyzer = IstatDataflowAnalyzer()
        
        result = analyzer.parse_dataflow_xml('missing.xml')
        
        assert result == {}
    
    def test_find_top_dataflows_by_category(self, capsys):
        """Test finding top dataflows by category."""
        analyzer = IstatDataflowAnalyzer()
        
        categorized_dataflows = {
            'popolazione': [
                {'id': '101_12', 'display_name': 'Pop 1', 'description': 'Desc 1', 'relevance_score': 10},
                {'id': '101_13', 'display_name': 'Pop 2', 'description': 'Desc 2', 'relevance_score': 8},
                {'id': '101_14', 'display_name': 'Pop 3', 'description': 'Desc 3', 'relevance_score': 6}
            ],
            'economia': [
                {'id': '163_156', 'display_name': 'Econ 1', 'description': 'Desc 1', 'relevance_score': 9}
            ],
            'altri': []
        }
        
        result = analyzer.find_top_dataflows_by_category(categorized_dataflows, top_n=2)
        
        assert len(result['popolazione']) == 2
        assert result['popolazione'][0]['id'] == '101_12'  # Highest score first
        assert result['popolazione'][1]['id'] == '101_13'
        
        assert len(result['economia']) == 1
        assert result['economia'][0]['id'] == '163_156'
        
        assert 'altri' not in result  # Empty categories should not be included
        
        # Check that output was printed
        captured = capsys.readouterr()
        assert 'TOP DATAFLOW PER CATEGORIA' in captured.out
    
    def test_create_tableau_ready_dataset_list(self, capsys):
        """Test creation of Tableau-ready dataset list."""
        analyzer = IstatDataflowAnalyzer()
        
        tested_dataflows = [
            {
                'id': '101_12',
                'name': 'Popolazione residente',
                'category': 'popolazione',
                'relevance_score': 10,
                'tests': {
                    'data_access': {'success': True, 'size_bytes': 2 * 1024 * 1024},
                    'observations_count': 1000
                }
            },
            {
                'id': '163_156',
                'name': 'PIL regionale',
                'category': 'economia',
                'relevance_score': 9,
                'tests': {
                    'data_access': {'success': False, 'size_bytes': 0}
                }
            }
        ]
        
        result = analyzer.create_tableau_ready_dataset_list(tested_dataflows)
        
        # Only successful datasets should be included
        assert len(result) == 1
        assert result[0]['dataflow_id'] == '101_12'
        assert result[0]['name'] == 'Popolazione residente'
        assert result[0]['category'] == 'popolazione'
        assert result[0]['data_size_mb'] == 2.0
        assert result[0]['observations_count'] == 1000
        assert 'sdmx_data_url' in result[0]
        assert 'tableau_connection_type' in result[0]
        assert 'refresh_frequency' in result[0]
        assert 'priority' in result[0]
        
        # Check output
        captured = capsys.readouterr()
        assert 'CREAZIONE LISTA DATASET TABLEAU-READY' in captured.out
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_generate_tableau_implementation_guide(self, mock_json_dump, mock_file):
        """Test generation of Tableau implementation guide."""
        analyzer = IstatDataflowAnalyzer()
        
        tableau_ready_datasets = [
            {
                'dataflow_id': '101_12',
                'name': 'Popolazione residente',
                'category': 'popolazione'
            }
        ]
        
        result = analyzer.generate_tableau_implementation_guide(tableau_ready_datasets)
        
        assert 'config_file' in result
        assert 'powershell_script' in result
        assert 'prep_flow' in result
        
        # Check that files were written
        assert mock_file.call_count >= 3  # At least 3 files should be written
        assert mock_json_dump.call_count >= 2  # At least 2 JSON files
    
    def test_generate_powershell_script(self):
        """Test PowerShell script generation."""
        analyzer = IstatDataflowAnalyzer()
        
        datasets = [
            {'dataflow_id': '101_12', 'name': 'Popolazione residente'},
            {'dataflow_id': '163_156', 'name': 'PIL regionale'}
        ]
        
        script = analyzer._generate_powershell_script(datasets)
        
        assert 'Download dataset ISTAT' in script
        assert '$baseUrl = "http://sdmx.istat.it/SDMXWS/rest/data/"' in script
        assert '101_12' in script
        assert '163_156' in script
        assert 'Start-Sleep -Seconds 2' in script
    
    def test_generate_prep_flow_template(self):
        """Test Tableau Prep flow template generation."""
        analyzer = IstatDataflowAnalyzer()
        
        datasets = [
            {'dataflow_id': '101_12', 'name': 'Popolazione residente'},
            {'dataflow_id': '163_156', 'name': 'PIL regionale'}
        ]
        
        template = analyzer._generate_prep_flow_template(datasets)
        
        assert template['name'] == 'ISTAT_Data_Integration_Flow'
        assert 'description' in template
        assert 'steps' in template
        assert len(template['steps']) > 0
        
        # Check step types
        step_types = [step['type'] for step in template['steps']]
        assert 'input' in step_types
        assert 'union' in step_types
        assert 'clean' in step_types
        assert 'output' in step_types