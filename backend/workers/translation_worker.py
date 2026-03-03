import logging
import time
import os
import asyncio
from sqlalchemy.orm import Session
from backend.services.worker_service import WorkerService

logger = logging.getLogger("translation-worker")

class TranslationWorker:
    """
    Translation Worker implementation using Mistral.
    Handles long-form text and document translation.
    """
    
    @staticmethod
    def run(
        task_id: str,
        input_data: Dict[str, Any],
        service: WorkerService,
        db: Session
    ) -> Dict[str, Any]:
        """
        Execute the translation workflow using Mistral.
        """
        return asyncio.run(TranslationWorker._execute_async(task_id, input_data, service))

    @staticmethod
    async def _execute_async(
        task_id: str,
        input_data: Dict[str, Any],
        service: WorkerService
    ) -> Dict[str, Any]:
        
        text = input_data.get("text")
        target_language = input_data.get("target_language", "Spanish")
        context = input_data.get("context", "General")
        
        if not text:
            return {"error": "No text provided for translation"}
        
        # Step 1: Initialize
        service.update_task_status(
            task_id,
            status="running",
            current_step=f"Preparing to translate to {target_language}...",
            steps_completed=1,
            steps_total=3
        )
        service.add_task_log(task_id, f"Translating content length {len(text)} chars to {target_language}")
        
        # Step 2: Call LLM
        service.update_task_status(
            task_id,
            status="running",
            current_step="Translating content...",
            steps_completed=2
        )
        
        from backend.lib.ai_client import get_ai_client
        client, model_name = get_ai_client(async_mode=True)
        
        system_prompt = f"""You are an expert translator. 
        Translate the following text to {target_language}.
        Preserve the original formatting, tone, and intent.
        Context: {context}
        Output ONLY the translated text, no preamble."""
        
        try:
            start_time = time.time()
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3
            )
            duration = time.time() - start_time
            
            translated_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            service.add_task_log(task_id, f"Translation completed in {duration:.1f}s using {tokens_used} tokens")
            
             # Step 3: Finalize
            service.update_task_status(
                task_id,
                status="completed",
                current_step="Done",
                steps_completed=3
            )
            
            return {
                "original_text": text,
                "translated_text": translated_text,
                "target_language": target_language,
                "summary": f"Translated content to {target_language}."
            }
            
        except Exception as e:
            logger.error(f"Error translating content: {e}")
            service.add_task_log(task_id, f"Translation Error: {str(e)}", level="error")
            raise e
