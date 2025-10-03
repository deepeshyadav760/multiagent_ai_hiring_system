# # Tool: Database operations
# from crewai_tools import BaseTool
# from typing import Dict, Any, List, Optional
# from database.mongodb_client import mongodb_sync
# from datetime import datetime
# from utils.logger import log
# import json


# class DatabaseTool(BaseTool):
#     name: str = "Database Operations"
#     description: str = """Performs database operations:
#     - Save candidate data
#     - Retrieve job postings
#     - Update candidate scores
#     - Query candidates by criteria
#     - Save interview records
#     """
    
#     def _run(self, action: str, collection: str, data: Optional[Dict] = None, query: Optional[Dict] = None) -> Dict[str, Any]:
#         """Execute database operation
        
#         Args:
#             action: Operation type (insert, find, update, delete)
#             collection: Collection name
#             data: Data to insert/update
#             query: Query filter
#         """
#         try:
#             coll = mongodb_sync.get_collection(collection)
            
#             if action == "insert":
#                 result = coll.insert_one(data)
#                 return {
#                     "success": True,
#                     "inserted_id": str(result.inserted_id),
#                     "message": f"Document inserted in {collection}"
#                 }
            
#             elif action == "find":
#                 documents = list(coll.find(query or {}).limit(100))
#                 # Convert ObjectId to string
#                 for doc in documents:
#                     if '_id' in doc:
#                         doc['_id'] = str(doc['_id'])
#                 return {
#                     "success": True,
#                     "documents": documents,
#                     "count": len(documents)
#                 }
            
#             elif action == "find_one":
#                 document = coll.find_one(query or {})
#                 if document and '_id' in document:
#                     document['_id'] = str(document['_id'])
#                 return {
#                     "success": True,
#                     "document": document
#                 }
            
#             elif action == "update":
#                 result = coll.update_one(query, {"$set": data})
#                 return {
#                     "success": True,
#                     "matched_count": result.matched_count,
#                     "modified_count": result.modified_count,
#                     "message": f"Updated {result.modified_count} document(s)"
#                 }
            
#             elif action == "update_many":
#                 result = coll.update_many(query, {"$set": data})
#                 return {
#                     "success": True,
#                     "matched_count": result.matched_count,
#                     "modified_count": result.modified_count
#                 }
            
#             elif action == "delete":
#                 result = coll.delete_one(query)
#                 return {
#                     "success": True,
#                     "deleted_count": result.deleted_count
#                 }
            
#             elif action == "count":
#                 count = coll.count_documents(query or {})
#                 return {
#                     "success": True,
#                     "count": count
#                 }
            
#             else:
#                 return {"success": False, "error": f"Unknown action: {action}"}
                
#         except Exception as e:
#             log.error(f"Database operation error: {e}")
#             return {"success": False, "error": str(e)}
    
#     def save_candidate(self, candidate_data: Dict) -> Dict[str, Any]:
#         """Save candidate to database"""
#         candidate_data['uploaded_at'] = datetime.utcnow()
#         candidate_data['updated_at'] = datetime.utcnow()
#         candidate_data['status'] = 'pending'
        
#         return self._run(
#             action="insert",
#             collection="candidates",
#             data=candidate_data
#         )
    
#     def update_candidate_score(self, email: str, score: float, matched_jobs: List[str]) -> Dict[str, Any]:
#         """Update candidate score and matched jobs"""
#         return self._run(
#             action="update",
#             collection="candidates",
#             query={"email": email},
#             data={
#                 "score": score,
#                 "matched_jobs": matched_jobs,
#                 "updated_at": datetime.utcnow()
#             }
#         )
    
#     def get_active_jobs(self) -> List[Dict]:
#         """Get all active job postings"""
#         result = self._run(
#             action="find",
#             collection="jobs",
#             query={"status": "active"}
#         )
#         return result.get("documents", [])
    
#     def get_job_by_id(self, job_id: str) -> Optional[Dict]:
#         """Get job by ID"""
#         result = self._run(
#             action="find_one",
#             collection="jobs",
#             query={"job_id": job_id}
#         )
#         return result.get("document")
    
#     def get_top_candidates(self, job_id: str, limit: int = 10) -> List[Dict]:
#         """Get top scoring candidates for a job"""
#         result = self._run(
#             action="find",
#             collection="candidates",
#             query={"matched_jobs": job_id}
#         )
        
#         candidates = result.get("documents", [])
#         # Sort by score
#         candidates.sort(key=lambda x: x.get('score', 0), reverse=True)
#         return candidates[:limit]
    
#     def save_interview(self, interview_data: Dict) -> Dict[str, Any]:
#         """Save interview record"""
#         interview_data['created_at'] = datetime.utcnow()
#         interview_data['updated_at'] = datetime.utcnow()
#         interview_data['status'] = 'scheduled'
        
#         return self._run(
#             action="insert",
#             collection="interviews",
#             data=interview_data
#         )


# # Create tool instance
# database_tool = DatabaseTool()



# tools/database_tool.py

from crewai_tools import BaseTool
from typing import Dict, Any, List, Optional
from database.mongodb_client import mongodb_sync
from datetime import datetime
from utils.logger import log
import json


class DatabaseTool(BaseTool):
    name: str = "Database Operations"
    description: str = """Performs database operations:
    - Save candidate data
    - Retrieve job postings
    - Update candidate scores
    - Query candidates by criteria
    - Save interview records
    """
    
    def _run(self, action: str, collection: str, data: Optional[Dict] = None, query: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute database operation
        
        Args:
            action: Operation type (insert, find, update, delete)
            collection: Collection name
            data: Data to insert/update
            query: Query filter
        """
        try:
            coll = mongodb_sync.get_collection(collection)
            
            if action == "insert":
                result = coll.insert_one(data)
                return {
                    "success": True,
                    "inserted_id": str(result.inserted_id),
                    "message": f"Document inserted in {collection}"
                }
            
            elif action == "find":
                documents = list(coll.find(query or {}).limit(100))
                # Convert ObjectId to string
                for doc in documents:
                    if '_id' in doc:
                        doc['_id'] = str(doc['_id'])
                return {
                    "success": True,
                    "documents": documents,
                    "count": len(documents)
                }
            
            elif action == "find_one":
                document = coll.find_one(query or {})
                if document and '_id' in document:
                    document['_id'] = str(document['_id'])
                return {
                    "success": True,
                    "document": document
                }
            
            elif action == "update":
                result = coll.update_one(query, {"$set": data})
                return {
                    "success": True,
                    "matched_count": result.matched_count,
                    "modified_count": result.modified_count,
                    "message": f"Updated {result.modified_count} document(s)"
                }
            
            elif action == "update_many":
                result = coll.update_many(query, {"$set": data})
                return {
                    "success": True,
                    "matched_count": result.matched_count,
                    "modified_count": result.modified_count
                }
            
            elif action == "delete":
                result = coll.delete_one(query)
                return {
                    "success": True,
                    "deleted_count": result.deleted_count
                }
            
            elif action == "count":
                count = coll.count_documents(query or {})
                return {
                    "success": True,
                    "count": count
                }
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            log.error(f"Database operation error: {e}")
            return {"success": False, "error": str(e)}
    
    def save_candidate(self, candidate_data: Dict) -> Dict[str, Any]:
        """Save candidate to database"""
        candidate_data['uploaded_at'] = datetime.utcnow()
        candidate_data['updated_at'] = datetime.utcnow()
        candidate_data['status'] = 'pending'
        
        return self._run(
            action="insert",
            collection="candidates",
            data=candidate_data
        )
    
    def update_candidate_score(self, email: str, score: float, matched_jobs: List[str]) -> Dict[str, Any]:
        """Update candidate score and matched jobs"""
        return self._run(
            action="update",
            collection="candidates",
            query={"email": email},
            data={
                "score": score,
                "matched_jobs": matched_jobs,
                "updated_at": datetime.utcnow()
            }
        )
    
    ### FIX: This method now fetches ALL jobs, solving the "score 0" issue. ###
    def get_active_jobs(self) -> List[Dict]:
        """
        Get all job postings. The incorrect 'status: active' filter was removed.
        """
        log.info("Fetching all job postings from the database.")
        # An empty query `{}` fetches all documents.
        result = self._run(
            action="find",
            collection="jobs",
            query={}
        )
        return result.get("documents", [])
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        """Get job by ID"""
        result = self._run(
            action="find_one",
            collection="jobs",
            query={"job_id": job_id}
        )
        return result.get("document")

    def get_interview_by_id(self, interview_id: str) -> Optional[Dict]:
        """Fetches a single interview document from the database by its ID."""
        log.info(f"Fetching interview by ID: {interview_id}")
        result = self._run(
            action="find_one",
            collection="interviews",
            query={"_id": interview_id}
        )
        return result.get("document")

    def get_top_candidates(self, job_id: str, limit: int = 10) -> List[Dict]:
        """Get top scoring candidates for a job"""
        result = self._run(
            action="find",
            collection="candidates",
            query={"matched_jobs": job_id}
        )
        
        candidates = result.get("documents", [])
        # Sort by score
        candidates.sort(key=lambda x: x.get('score', 0), reverse=True)
        return candidates[:limit]
    
    def save_interview(self, interview_data: Dict) -> Dict[str, Any]:
        """Save interview record"""
        interview_data['created_at'] = datetime.utcnow()
        interview_data['updated_at'] = datetime.utcnow()
        interview_data['status'] = 'scheduled'
        
        return self._run(
            action="insert",
            collection="interviews",
            data=interview_data
        )


# Create tool instance
database_tool = DatabaseTool()