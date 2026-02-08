"""
Legal Resources Module

Manages legal resources with FDO (Fair Digital Object) principles,
JSON-LD formatting, and PID (Persistent Identifier) support.
"""

import json
import uuid
import os
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from logger_config import setup_logger, get_trace_id
from errors import InvalidParamsError

# Initialize logger
logger = setup_logger()

# Constants
PID_FILE_PATH = "pids.json"
MCP_LEGAL_PREFIX = "legal://"
PID_PREFIX = "legal://pid/"

class LegalResourceProvider:
    """
    Provider for legal resources with FDO and PID support.
    """
    
    def __init__(self, pid_file_path: str = PID_FILE_PATH):
        self.pid_file_path = pid_file_path
        self._pids: Dict[str, Dict[str, Any]] = self._load_pids()
        self._resources = {
             "legal://civil-code/contract": {
                "name": "《民法典》合同编",
                "description": "中国民法典合同编相关条文",
                "mimeType": "application/json+ld",
                "loader": self._get_civil_code_contract
            },
            "legal://templates/contract-checklist": {
                "name": "合同审查清单",
                "description": "标准合同审查要点清单",
                "mimeType": "application/json+ld",
                "loader": self._get_contract_checklist
            },
             "legal://rules/penalty-assessment": {
                 "name": "违约金评估规则",
                 "description": "违约金过高判定标准和计算方法",
                 "mimeType": "application/json+ld",
                 "loader": self._get_penalty_rules
             },
             "legal://judicial-discretion/standards": {
                 "name": "司法裁量权基准",
                 "description": "基于《九民纪要》与司法解释的裁量权行使标准",
                 "mimeType": "application/json+ld",
                 "loader": self._get_judicial_discretion_standards
             }
         }
    
    def _load_pids(self) -> Dict[str, Dict[str, Any]]:
        """Load PIDs from persistent storage."""
        if os.path.exists(self.pid_file_path):
            try:
                with open(self.pid_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load PIDs from {self.pid_file_path}: {e}")
                return {}
        return {}

    def _save_pids(self):
        """Save PIDs to persistent storage."""
        try:
            with open(self.pid_file_path, 'w', encoding='utf-8') as f:
                json.dump(self._pids, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save PIDs to {self.pid_file_path}: {e}")

    def generate_pid(self, content: Any, metadata: Dict[str, Any], parent_pid: Optional[str] = None) -> str:
        """
        Generate a persistent identifier (PID) for a resource.
        Currently uses a simple UUID-based handle mechanism.
        
        Args:
            content: The content of the resource.
            metadata: Metadata associated with the resource.
            parent_pid: Optional PID of the parent resource (for chaining).
        """
        handle = str(uuid.uuid4())
        pid_uri = f"{PID_PREFIX}{handle}"
        
        # Calculate content hash for integrity
        content_str = json.dumps(content, sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
        
        record = {
            "handle": handle,
            "uri": pid_uri,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata,
            "content_hash": content_hash,
            "parent_pid": parent_pid,
            # In a real system, we might store the content reference or the content itself if small
            # For this implementation, we'll store the content if it's a dynamic report
            "content": content
        }
        
        self._pids[handle] = record
        self._save_pids()
        
        logger.info(f"Generated PID: {pid_uri} (Parent: {parent_pid})", extra={"trace_id": get_trace_id()})
        return pid_uri

    def get_resource_by_pid(self, pid_uri: str) -> Optional[Dict[str, Any]]:
        """Retrieve a resource using its PID."""
        if not pid_uri.startswith(PID_PREFIX):
             return None
             
        handle = pid_uri[len(PID_PREFIX):]
        record = self._pids.get(handle)
        
        if not record:
            return None
            
        return record.get("content")

    def list_resources(self) -> List[Dict[str, Any]]:
        """List all available static resources."""
        return [
            {
                "uri": uri,
                "name": meta["name"],
                "description": meta["description"],
                "mimeType": meta["mimeType"]
            }
            for uri, meta in self._resources.items()
        ]

    def get_resource_content(self, uri: str) -> str:
        """
        Get resource content by URI.
        Supports both static resources (legal://...) and PIDs (legal://pid/...).
        Returns JSON-LD formatted string.
        """
        trace_id = get_trace_id()
        
        # Check if it's a PID
        if uri.startswith(PID_PREFIX):
            content = self.get_resource_by_pid(uri)
            if content is None:
                raise InvalidParamsError(f"PID not found: {uri}")
            return self.format_as_jsonld(content, uri, "ComplianceReport") # Assuming mostly reports for now

        # Check if it's a static resource
        resource_meta = self._resources.get(uri)
        if resource_meta:
             content = resource_meta["loader"]()
             return self.format_as_jsonld(content, uri, "Legislation") # Simplified type mapping

        raise InvalidParamsError(f"Unknown resource: {uri}")

    def format_as_jsonld(self, data: Any, uri: str, type_hint: str = "Thing") -> str:
        """
        Wrap data in JSON-LD format with FDO metadata.
        """
        
        jsonld = {
            "@context": "https://schema.org",
            "@type": type_hint,
            "@id": uri,
            "dateCreated": datetime.utcnow().isoformat() + "Z",
            "mainEntity": data
        }

        # If it's a PID resource, add provenance if available
        if uri.startswith(PID_PREFIX):
             handle = uri[len(PID_PREFIX):]
             record = self._pids.get(handle)
             if record and record.get("parent_pid"):
                 jsonld["isPartOf"] = {
                     "@type": "CreativeWork",
                     "@id": record["parent_pid"]
                 }
        
        return json.dumps(jsonld, ensure_ascii=False, indent=2)

    # --- Resource Loaders (Migrated from server.py) ---

    def _get_civil_code_contract(self) -> Dict[str, Any]:
        """Get Civil Code Contract section content."""
        return {
            "title": "中华人民共和国民法典 - 合同编 (摘要)",
            "articles": [
                {
                    "id": "585",
                    "title": "违约金",
                    "content": "当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金..."
                },
                {
                    "id": "506",
                    "title": "免责条款的效力",
                    "content": "合同中的下列免责条款无效: (一) 造成对方人身损害的; (二) 因故意..."
                },
                {
                    "id": "577",
                    "title": "违约责任",
                    "content": "当事人一方不履行合同义务或者履行合同义务不符合约定的..."
                }
            ]
        }

    def _get_contract_checklist(self) -> Dict[str, Any]:
        """Get Contract Review Checklist."""
        return {
            "基本信息审查": [
                "合同各方主体资格是否合法",
                "合同名称是否准确反映合同性质",
                "合同签订日期和生效日期是否明确"
            ],
            "主要条款审查": [
                "合同标的是否明确",
                "数量、质量标准是否清晰",
                "价款或报酬及支付方式是否约定",
                "履行期限、地点和方式是否明确"
            ],
            "风险条款审查": [
                "违约责任是否约定",
                "争议解决方式是否明确",
                "保密条款是否完善",
                "知识产权归属是否清晰"
            ],
            "合规性审查": [
                "是否违反法律强制性规定",
                "免责条款是否有效",
                "管辖权约定是否合法",
                "是否需要政府审批或备案"
            ]
        }

    def _get_penalty_rules(self) -> Dict[str, Any]:
        """Get Penalty Assessment Rules."""
        return {
            "法律依据": "《民法典》第585条",
            "基本原则": "违约金应当与实际损失相当,不得过分高于实际损失",
            "司法实践标准": {
                "一般标准": "违约金不超过实际损失的30%",
                "特殊情况": "在某些商事合同中,可能允许更高比例",
                "调整机制": "当事人可以请求法院或仲裁机构调整过高或过低的违约金"
            },
            "计算方法": [
                "按合同总价款的百分比计算",
                "按日计算 (如每日万分之五)",
                "按实际损失的倍数计算"
            ],
            "注意事项": [
                "违约金与损害赔偿不能同时主张",
                "违约金过高的举证责任在违约方",
                "可以约定违约金的上限"
            ]
        }

    def _get_judicial_discretion_standards(self) -> Dict[str, Any]:
        """Get Judicial Discretion Standards."""
        return {
            "title": "司法裁量权行使基准",
            "source": "《全国法院民商事审判工作会议纪要》（九民纪要）及相关司法解释",
            "factors": {
                "loss": {
                    "name": "实际损失",
                    "description": "违约行为造成的直接损失和可得利益损失",
                    "weight": "基础基准"
                },
                "performance": {
                    "name": "合同履行情况",
                    "description": "已履行部分占合同总义务的比例",
                    "impact": "负相关 (履行越多，违约金调整幅度越大)"
                },
                "fault": {
                    "name": "当事人过错程度",
                    "description": "违约方的主观恶意程度 (故意、重大过失、轻微过失)",
                    "impact": "正相关 (过错越大，违约金可能越高)"
                }
            },
            "formula_reference": "V_final = f(Loss, Performance, Fault)",
            "guidelines": [
                "以实际损失为基础，兼顾合同的履行情况、当事人的过错程度以及预期利益等综合因素",
                "约定的违约金超过造成损失的百分之三十的，一般可以认定为过分高于造成的损失"
            ]
        }
