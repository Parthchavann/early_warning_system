import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import faiss
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
import logging
import json
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class PatientEmbeddingGenerator:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.text_encoder = SentenceTransformer(model_name)
        self.embedding_dim = self.text_encoder.get_sentence_embedding_dimension()
        
    def encode_clinical_notes(self, notes: List[str]) -> np.ndarray:
        if not notes:
            return np.zeros((1, self.embedding_dim))
            
        embeddings = self.text_encoder.encode(notes, normalize_embeddings=True)
        
        if len(embeddings.shape) == 1:
            embeddings = embeddings.reshape(1, -1)
            
        return embeddings
    
    def create_patient_profile_embedding(
        self,
        demographics: Dict[str, Any],
        vitals_summary: Dict[str, float],
        lab_summary: Dict[str, float],
        clinical_notes: List[str]
    ) -> np.ndarray:
        
        demographic_text = self._demographics_to_text(demographics)
        vitals_text = self._vitals_to_text(vitals_summary)
        lab_text = self._labs_to_text(lab_summary)
        
        all_text = [demographic_text, vitals_text, lab_text] + clinical_notes
        text_to_encode = " ".join([t for t in all_text if t])
        
        if not text_to_encode.strip():
            return np.zeros(self.embedding_dim)
            
        embedding = self.text_encoder.encode([text_to_encode], normalize_embeddings=True)
        return embedding[0]
    
    def _demographics_to_text(self, demographics: Dict[str, Any]) -> str:
        parts = []
        
        age = demographics.get('age')
        if age:
            if age < 18:
                parts.append("pediatric patient")
            elif age < 65:
                parts.append("adult patient")
            else:
                parts.append("elderly patient")
                
        gender = demographics.get('gender')
        if gender:
            parts.append(f"{gender} patient")
            
        diagnosis = demographics.get('primary_diagnosis')
        if diagnosis:
            parts.append(f"diagnosed with {diagnosis}")
            
        comorbidities = demographics.get('comorbidities', [])
        if comorbidities:
            parts.append(f"comorbidities include {', '.join(comorbidities)}")
            
        return " ".join(parts)
    
    def _vitals_to_text(self, vitals: Dict[str, float]) -> str:
        parts = []
        
        hr = vitals.get('heart_rate_mean')
        if hr:
            if hr > 100:
                parts.append("tachycardic")
            elif hr < 60:
                parts.append("bradycardic")
            else:
                parts.append("normal heart rate")
                
        bp_sys = vitals.get('blood_pressure_systolic_mean')
        if bp_sys:
            if bp_sys > 140:
                parts.append("hypertensive")
            elif bp_sys < 90:
                parts.append("hypotensive")
            else:
                parts.append("normal blood pressure")
                
        temp = vitals.get('temperature_mean')
        if temp:
            if temp > 38.0:
                parts.append("febrile")
            elif temp < 36.0:
                parts.append("hypothermic")
                
        rr = vitals.get('respiratory_rate_mean')
        if rr and rr > 20:
            parts.append("tachypneic")
            
        return " ".join(parts)
    
    def _labs_to_text(self, labs: Dict[str, float]) -> str:
        parts = []
        
        wbc = labs.get('wbc_current')
        if wbc:
            if wbc > 12000:
                parts.append("elevated white blood cells")
            elif wbc < 4000:
                parts.append("low white blood cells")
                
        lactate = labs.get('lactate_current')
        if lactate and lactate > 2.0:
            parts.append("elevated lactate")
            
        creatinine = labs.get('creatinine_current')
        if creatinine and creatinine > 1.2:
            parts.append("elevated creatinine")
            
        return " ".join(parts)

class FAISSVectorStore:
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.patient_metadata = {}
        self.id_to_patient = {}
        
    def add_patient(
        self,
        patient_id: str,
        embedding: np.ndarray,
        metadata: Dict[str, Any]
    ):
        if embedding.shape[0] != self.dimension:
            raise ValueError(f"Embedding dimension {embedding.shape[0]} doesn't match index dimension {self.dimension}")
            
        embedding = embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(embedding)
        
        idx = self.index.ntotal
        self.index.add(embedding)
        
        self.patient_metadata[idx] = metadata
        self.id_to_patient[idx] = patient_id
        
        logger.debug(f"Added patient {patient_id} to vector store")
    
    def search_similar_patients(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        
        if self.index.ntotal == 0:
            return []
            
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        scores, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score >= threshold:
                patient_id = self.id_to_patient[idx]
                metadata = self.patient_metadata[idx].copy()
                metadata['similarity_score'] = float(score)
                metadata['patient_id'] = patient_id
                results.append(metadata)
                
        return sorted(results, key=lambda x: x['similarity_score'], reverse=True)
    
    def save_index(self, filepath: str):
        faiss.write_index(self.index, f"{filepath}.faiss")
        
        with open(f"{filepath}_metadata.json", 'w') as f:
            json.dump({
                'patient_metadata': self.patient_metadata,
                'id_to_patient': self.id_to_patient
            }, f, default=str)
            
        logger.info(f"FAISS index saved to {filepath}")
    
    def load_index(self, filepath: str):
        self.index = faiss.read_index(f"{filepath}.faiss")
        
        with open(f"{filepath}_metadata.json", 'r') as f:
            data = json.load(f)
            self.patient_metadata = {int(k): v for k, v in data['patient_metadata'].items()}
            self.id_to_patient = {int(k): v for k, v in data['id_to_patient'].items()}
            
        logger.info(f"FAISS index loaded from {filepath}")

class QdrantVectorStore:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "patient_embeddings"
    ):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        
    def initialize_collection(self, dimension: int):
        try:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Initialized Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error initializing Qdrant collection: {e}")
            raise
    
    def add_patient(
        self,
        patient_id: str,
        embedding: np.ndarray,
        metadata: Dict[str, Any]
    ):
        try:
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload={
                    "patient_id": patient_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    **metadata
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.debug(f"Added patient {patient_id} to Qdrant")
            
        except Exception as e:
            logger.error(f"Error adding patient to Qdrant: {e}")
            raise
    
    def search_similar_patients(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=k,
                score_threshold=threshold,
                query_filter=filters
            )
            
            results = []
            for hit in search_result:
                result = hit.payload.copy()
                result['similarity_score'] = hit.score
                results.append(result)
                
            return results
            
        except Exception as e:
            logger.error(f"Error searching in Qdrant: {e}")
            return []

class PatientSimilarityService:
    def __init__(
        self,
        use_qdrant: bool = True,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333
    ):
        self.embedding_generator = PatientEmbeddingGenerator()
        self.use_qdrant = use_qdrant
        
        if use_qdrant:
            self.vector_store = QdrantVectorStore(qdrant_host, qdrant_port)
            try:
                self.vector_store.initialize_collection(self.embedding_generator.embedding_dim)
            except:
                logger.warning("Could not connect to Qdrant, falling back to FAISS")
                self.use_qdrant = False
                
        if not self.use_qdrant:
            self.vector_store = FAISSVectorStore(self.embedding_generator.embedding_dim)
    
    def index_patient(
        self,
        patient_id: str,
        demographics: Dict[str, Any],
        vitals_summary: Dict[str, float],
        lab_summary: Dict[str, float],
        clinical_notes: List[str]
    ):
        
        embedding = self.embedding_generator.create_patient_profile_embedding(
            demographics, vitals_summary, lab_summary, clinical_notes
        )
        
        metadata = {
            'demographics': demographics,
            'vitals_summary': vitals_summary,
            'lab_summary': lab_summary,
            'num_notes': len(clinical_notes),
            'indexed_at': datetime.utcnow().isoformat()
        }
        
        self.vector_store.add_patient(patient_id, embedding, metadata)
    
    def find_similar_patients(
        self,
        target_patient_id: str,
        demographics: Dict[str, Any],
        vitals_summary: Dict[str, float],
        lab_summary: Dict[str, float],
        clinical_notes: List[str],
        k: int = 5,
        similarity_threshold: float = 0.75
    ) -> List[Dict[str, Any]]:
        
        query_embedding = self.embedding_generator.create_patient_profile_embedding(
            demographics, vitals_summary, lab_summary, clinical_notes
        )
        
        similar_patients = self.vector_store.search_similar_patients(
            query_embedding, k=k, threshold=similarity_threshold
        )
        
        filtered_patients = [
            p for p in similar_patients 
            if p.get('patient_id') != target_patient_id
        ]
        
        return filtered_patients
    
    def get_cohort_insights(
        self,
        similar_patients: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        
        if not similar_patients:
            return {'message': 'No similar patients found'}
            
        insights = {
            'cohort_size': len(similar_patients),
            'average_similarity': np.mean([p['similarity_score'] for p in similar_patients]),
            'demographics_distribution': {},
            'common_diagnoses': {},
            'risk_patterns': {}
        }
        
        demographics_list = [p.get('demographics', {}) for p in similar_patients]
        
        age_groups = [self._categorize_age(d.get('age', 50)) for d in demographics_list]
        insights['demographics_distribution']['age_groups'] = dict(pd.Series(age_groups).value_counts())
        
        diagnoses = [d.get('primary_diagnosis', 'Unknown') for d in demographics_list]
        insights['common_diagnoses'] = dict(pd.Series(diagnoses).value_counts().head(5))
        
        return insights
    
    def _categorize_age(self, age: int) -> str:
        if age < 18:
            return 'pediatric'
        elif age < 65:
            return 'adult'
        else:
            return 'elderly'