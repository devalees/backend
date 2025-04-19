import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from Apps.documents.models import Document, DocumentClassification, DocumentTag
from Apps.entity.models import Organization

User = get_user_model()

class DocumentFilteringTestCase(TestCase):
    """Test case for document filtering and aggregation"""
    
    def setUp(self):
        """Set up test data"""
        # Create test organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            description='Test Organization Description'
        )

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test document classifications
        self.classification1 = DocumentClassification.objects.create(
            name='Reports',
            description='All reports',
            organization=self.organization
        )
        
        self.classification2 = DocumentClassification.objects.create(
            name='Contracts',
            description='Legal contracts',
            organization=self.organization
        )
        
        # Create test document tags
        self.tag1 = DocumentTag.objects.create(
            name='Important',
            description='Important documents',
            color='#ff0000',
            organization=self.organization
        )
        
        self.tag2 = DocumentTag.objects.create(
            name='Draft',
            description='Draft documents',
            color='#0000ff',
            organization=self.organization
        )
        
        # Create test documents
        self.doc1 = Document.objects.create(
            title='Annual Report 2023',
            description='Annual financial report for 2023',
            status='approved',
            user=self.user,
            classification=self.classification1,
            organization=self.organization
        )
        self.doc1.tags.add(self.tag1)
        
        self.doc2 = Document.objects.create(
            title='Q1 Report 2023',
            description='Q1 financial report for 2023',
            status='draft',
            user=self.user,
            classification=self.classification1,
            organization=self.organization
        )
        self.doc2.tags.add(self.tag2)
        
        self.doc3 = Document.objects.create(
            title='Service Contract',
            description='Service agreement with vendor',
            status='approved',
            user=self.user,
            classification=self.classification2,
            organization=self.organization
        )
        self.doc3.tags.add(self.tag1)
        
        # Setup API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # API URLs
        self.filter_url = reverse('documents:document-filter')
        self.aggregate_url = reverse('documents:document-aggregate')
    
    def test_document_filter_by_title(self):
        """Test filtering documents by title"""
        # Filter documents with 'Report' in title
        filters = {'title': 'Report'}
        filtered_docs = Document.filter(filters)
        
        # Check that only the two report documents are returned
        self.assertEqual(filtered_docs.count(), 2)
        self.assertIn(self.doc1, filtered_docs)
        self.assertIn(self.doc2, filtered_docs)
        self.assertNotIn(self.doc3, filtered_docs)
    
    def test_document_filter_by_status(self):
        """Test filtering documents by status"""
        # Filter documents with status 'approved'
        filters = {'status': 'approved'}
        filtered_docs = Document.filter(filters)
        
        # Check that only approved documents are returned
        self.assertEqual(filtered_docs.count(), 2)
        self.assertIn(self.doc1, filtered_docs)
        self.assertIn(self.doc3, filtered_docs)
        self.assertNotIn(self.doc2, filtered_docs)
    
    def test_document_filter_by_classification(self):
        """Test filtering documents by classification"""
        # Filter documents with classification 'Reports'
        filters = {'classification': self.classification1}
        filtered_docs = Document.filter(filters)
        
        # Check that only documents with Reports classification are returned
        self.assertEqual(filtered_docs.count(), 2)
        self.assertIn(self.doc1, filtered_docs)
        self.assertIn(self.doc2, filtered_docs)
        self.assertNotIn(self.doc3, filtered_docs)
    
    def test_document_filter_by_tag(self):
        """Test filtering documents by tag"""
        # Filter documents with 'Important' tag
        # Use the filter_by_related utility method since tags is a ManyToMany field
        filtered_docs = Document.objects.filter(tags=self.tag1)
        
        # Check that only documents with Important tag are returned
        self.assertEqual(filtered_docs.count(), 2)
        self.assertIn(self.doc1, filtered_docs)
        self.assertIn(self.doc3, filtered_docs)
        self.assertNotIn(self.doc2, filtered_docs)
    
    def test_document_aggregate_by_status(self):
        """Test aggregating documents by status"""
        # Aggregate documents by status
        aggregations = {'id': 'count'}
        group_by = ['status']
        
        result = Document.aggregate(aggregations, group_by)
        
        # Check that the aggregation results are correct
        self.assertEqual(len(result), 2)  # Two distinct statuses
        
        # Convert result to dict for easier testing
        result_dict = {item['status']: item['id__count'] for item in result}
        
        # Check counts
        self.assertEqual(result_dict['approved'], 2)  # Two approved documents
        self.assertEqual(result_dict['draft'], 1)  # One draft document
    
    def test_document_aggregate_by_classification(self):
        """Test aggregating documents by classification"""
        # Aggregate documents by classification
        aggregations = {'id': 'count'}
        group_by = ['classification']
        
        result = Document.aggregate(aggregations, group_by)
        
        # Check that the aggregation results are correct
        self.assertEqual(len(result), 2)  # Two distinct classifications
        
        # Convert result to dict for easier testing
        # Note: classification_id might be used in the result instead of classification
        result_dict = {}
        for item in result:
            key = item.get('classification', item.get('classification_id'))
            result_dict[key] = item['id__count']
        
        # Check counts
        self.assertEqual(result_dict.get(self.classification1.id), 2)  # Two Reports documents
        self.assertEqual(result_dict.get(self.classification2.id), 1)  # One Contracts document
    
    def test_api_document_filter(self):
        """Test document filtering through API"""
        # Make API request to filter documents with 'Report' in title
        response = self.client.post(
            self.filter_url,
            {'title': 'Report'},
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Get document ids from response
        doc_ids = [item['id'] for item in response.data]
        
        # Check that the correct documents are returned
        self.assertIn(self.doc1.id, doc_ids)
        self.assertIn(self.doc2.id, doc_ids)
        self.assertNotIn(self.doc3.id, doc_ids)
    
    def test_api_document_aggregate(self):
        """Test document aggregation through API"""
        # Make API request to aggregate documents by status
        response = self.client.post(
            self.aggregate_url,
            {
                'aggregations': {'id': 'count'},
                'group_by': ['status']
            },
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check aggregation results
        result = response.data['results']
        self.assertEqual(len(result), 2)  # Two distinct statuses
        
        # Convert result to dict for easier testing
        result_dict = {item['status']: item['id__count'] for item in result}
        
        # Check counts
        self.assertEqual(result_dict['approved'], 2)  # Two approved documents
        self.assertEqual(result_dict['draft'], 1)  # One draft document 