"""
Base Pipeline Interface

Defines the common interface and functionality for all pipeline components.
All pipeline implementations should inherit from BasePipeline to ensure consistency.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import logging


@dataclass
class PipelineResult:
    """Standard result object for pipeline operations"""
    success: bool
    data: Dict[str, Any]
    errors: List[str]
    duration: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "errors": self.errors,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class PipelineState:
    """Pipeline state tracking"""
    pipeline_name: str
    status: str  # "ready", "running", "success", "error"
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_name": self.pipeline_name,
            "status": self.status,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineState":
        return cls(
            pipeline_name=data["pipeline_name"],
            status=data["status"],
            last_run=datetime.fromisoformat(data["last_run"]) if data.get("last_run") else None,
            last_success=datetime.fromisoformat(data["last_success"]) if data.get("last_success") else None,
            run_count=data.get("run_count", 0),
            error_count=data.get("error_count", 0),
            last_error=data.get("last_error"),
            metadata=data.get("metadata", {})
        )


class StateManager:
    """Manages pipeline state persistence"""
    
    def __init__(self, state_file: Path = None):
        self.state_file = state_file or Path(".pipeline-state.json")
        self.logger = logging.getLogger(__name__)
    
    def load_state(self, pipeline_name: str) -> PipelineState:
        """Load state for a specific pipeline"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    all_states = json.load(f)
                
                if pipeline_name in all_states:
                    return PipelineState.from_dict(all_states[pipeline_name])
        except Exception as e:
            self.logger.warning(f"Failed to load state for {pipeline_name}: {e}")
        
        # Return default state if loading fails
        return PipelineState(
            pipeline_name=pipeline_name,
            status="ready"
        )
    
    def save_state(self, state: PipelineState) -> None:
        """Save state for a pipeline"""
        try:
            # Load existing states
            all_states = {}
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    all_states = json.load(f)
            
            # Update state for this pipeline
            all_states[state.pipeline_name] = state.to_dict()
            
            # Write back to file
            with open(self.state_file, 'w') as f:
                json.dump(all_states, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save state for {state.pipeline_name}: {e}")
    
    def get_all_states(self) -> Dict[str, PipelineState]:
        """Get all pipeline states"""
        states = {}
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    all_states = json.load(f)
                
                for name, state_data in all_states.items():
                    states[name] = PipelineState.from_dict(state_data)
        except Exception as e:
            self.logger.warning(f"Failed to load all states: {e}")
        
        return states


class BasePipeline(ABC):
    """Base class for all pipeline implementations"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.state_manager = StateManager()
        self._state = self.state_manager.load_state(name)
    
    @property
    def state(self) -> PipelineState:
        """Get current pipeline state"""
        return self._state
    
    def _update_state(self, status: str, error: str = None, metadata: Dict[str, Any] = None):
        """Update pipeline state"""
        now = datetime.now()
        self._state.status = status
        self._state.last_run = now
        self._state.run_count += 1
        
        if error:
            self._state.error_count += 1
            self._state.last_error = error
        else:
            self._state.last_success = now
            self._state.last_error = None
        
        if metadata:
            self._state.metadata.update(metadata)
        
        self.state_manager.save_state(self._state)
    
    def run(self, **kwargs) -> PipelineResult:
        """Execute the pipeline"""
        start_time = datetime.now()
        self._update_state("running")
        
        try:
            self.logger.info(f"Starting {self.name} pipeline execution")
            
            # Validate inputs
            self.validate_inputs(**kwargs)
            
            # Execute main pipeline logic
            result_data = self.execute(**kwargs)
            
            # Validate outputs
            self.validate_outputs(result_data)
            
            duration = (datetime.now() - start_time).total_seconds()
            result = PipelineResult(
                success=True,
                data=result_data,
                errors=[],
                duration=duration,
                timestamp=start_time
            )
            
            self._update_state("success", metadata={"last_result": result_data})
            self.logger.info(f"{self.name} pipeline completed successfully in {duration:.2f}s")
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            result = PipelineResult(
                success=False,
                data={},
                errors=[error_msg],
                duration=duration,
                timestamp=start_time
            )
            
            self._update_state("error", error=error_msg)
            self.logger.error(f"{self.name} pipeline failed after {duration:.2f}s: {error_msg}")
            
            return result
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Main pipeline execution logic - must be implemented by subclasses"""
        pass
    
    def validate_inputs(self, **kwargs) -> None:
        """Validate pipeline inputs - can be overridden by subclasses"""
        pass
    
    def validate_outputs(self, result_data: Dict[str, Any]) -> None:
        """Validate pipeline outputs - can be overridden by subclasses"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed pipeline status"""
        return {
            "name": self.name,
            "state": self.state.to_dict(),
            "config": self.config
        }