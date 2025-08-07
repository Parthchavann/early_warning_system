import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from confluent_kafka import Consumer, KafkaError, KafkaException
from confluent_kafka.serialization import StringDeserializer
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class VitalsKafkaConsumer:
    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str = "ews-consumer-group",
        auto_offset_reset: str = "latest"
    ):
        self.config = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': auto_offset_reset,
            'enable.auto.commit': True,
            'session.timeout.ms': 6000,
            'max.poll.interval.ms': 300000
        }
        self.consumer = Consumer(self.config)
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=10)
        
    def subscribe(self, topics: list):
        self.consumer.subscribe(topics)
        logger.info(f"Subscribed to topics: {topics}")
        
    async def process_vital_signs(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            patient_id = message.get('patient_id')
            vitals = message.get('vitals', {})
            timestamp = datetime.fromisoformat(message.get('timestamp'))
            
            processed_vitals = {
                'patient_id': patient_id,
                'timestamp': timestamp,
                'heart_rate': vitals.get('heart_rate'),
                'blood_pressure_systolic': vitals.get('bp_systolic'),
                'blood_pressure_diastolic': vitals.get('bp_diastolic'),
                'respiratory_rate': vitals.get('respiratory_rate'),
                'temperature': vitals.get('temperature'),
                'oxygen_saturation': vitals.get('spo2'),
                'glasgow_coma_scale': vitals.get('gcs')
            }
            
            processed_vitals = {k: v for k, v in processed_vitals.items() if v is not None}
            
            logger.debug(f"Processed vitals for patient {patient_id}")
            return processed_vitals
            
        except Exception as e:
            logger.error(f"Error processing vital signs: {e}")
            return None
            
    async def process_clinical_notes(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            patient_id = message.get('patient_id')
            note = message.get('note', {})
            timestamp = datetime.fromisoformat(message.get('timestamp'))
            
            processed_note = {
                'patient_id': patient_id,
                'timestamp': timestamp,
                'author_id': note.get('author_id'),
                'author_role': note.get('author_role'),
                'note_type': note.get('type'),
                'content': note.get('content')
            }
            
            logger.debug(f"Processed clinical note for patient {patient_id}")
            return processed_note
            
        except Exception as e:
            logger.error(f"Error processing clinical note: {e}")
            return None
            
    async def consume_messages(
        self,
        process_callback: Callable,
        error_callback: Optional[Callable] = None
    ):
        self.running = True
        
        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                    
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"End of partition reached {msg.partition()}")
                    elif error_callback:
                        await error_callback(msg.error())
                    else:
                        logger.error(f"Kafka error: {msg.error()}")
                    continue
                    
                try:
                    value = json.loads(msg.value().decode('utf-8'))
                    topic = msg.topic()
                    
                    if 'vitals' in topic:
                        processed = await self.process_vital_signs(value)
                    elif 'notes' in topic:
                        processed = await self.process_clinical_notes(value)
                    else:
                        processed = value
                        
                    if processed:
                        await process_callback(processed, topic)
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        finally:
            self.stop()
            
    def stop(self):
        self.running = False
        self.consumer.close()
        self.executor.shutdown(wait=True)
        logger.info("Kafka consumer stopped")

class StreamProcessor:
    def __init__(self, consumer: VitalsKafkaConsumer):
        self.consumer = consumer
        self.buffer = {}
        self.window_size = 60
        
    async def process_stream(self, data: Dict[str, Any], topic: str):
        patient_id = data.get('patient_id')
        
        if patient_id not in self.buffer:
            self.buffer[patient_id] = []
            
        self.buffer[patient_id].append(data)
        
        if len(self.buffer[patient_id]) > self.window_size:
            self.buffer[patient_id] = self.buffer[patient_id][-self.window_size:]
            
        await self.analyze_patient_data(patient_id)
        
    async def analyze_patient_data(self, patient_id: str):
        data_points = self.buffer.get(patient_id, [])
        
        if len(data_points) < 5:
            return
            
        logger.info(f"Analyzing data for patient {patient_id}, {len(data_points)} data points")