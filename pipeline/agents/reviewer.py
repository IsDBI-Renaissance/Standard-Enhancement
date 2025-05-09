"""
Reviewer agent for the AAOIFI Standards Enhancement System.
"""

from typing import Dict, Any, Optional, List
import logging

from langchain.llms.base import BaseLLM
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from pipeline.agents.base_agent import BaseAgent
from pipeline.models.models import KnowledgeRequest

class ReviewerOutput(BaseModel):
    """
    Output from the reviewer agent.
    """
    reviewed_text: str = Field(description="The reviewed text of the standard")
    quality_score: int = Field(description="The quality score for the review (0-100)")
    notes: str = Field(description="Notes about the review")
    shariah_issues: List[str] = Field(default_factory=list, description="List of Shariah compliance issues in the standard")
    clarity_issues: List[str] = Field(default_factory=list, description="List of clarity issues in the standard")
    structure_issues: List[str] = Field(default_factory=list, description="List of structural issues in the standard")
    needs_knowledge: bool = Field(False, description="Whether external knowledge is needed")
    knowledge_query: Optional[str] = Field(None, description="The query to use for knowledge retrieval")

class Reviewer(BaseAgent):
    """
    Reviews the AAOIFI standard for quality and Shariah compliance.
    """
    def __init__(self, llm: BaseLLM):
        super().__init__(
            llm=llm,
            name="reviewer",
            stage_description="Evaluates quality and Shariah compliance",
        )
        self.parser = PydanticOutputParser(pydantic_object=ReviewerOutput)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a specialized AI assistant that reviews AAOIFI standards. Your job is to:

1. Check if the standard is clear, structured, and complete.
2. Ensure it aligns with Shariah principles.
3. Highlight issues with Shariah compliance, clarity, or structure.
4. Give a quality score (0-100).

If external knowledge is needed, mention it in your response.

Output format:

```
Reviewed text: (Corrected text of the standard)
Quality score: (Score from 0-100)
Notes: (Summary of the review)
Shariah issues: (List of Shariah compliance issues)
Clarity issues: (List of clarity issues)
Structure issues: (List of structure issues)
Needs knowledge: (true/false)
Knowledge query: (Query for additional information if needed)
```

Be fair and thorough. Standards scoring below 50 will be sent back for revision.

{format_instructions}
"""),
            ("human", "Here is the preprocessed AAOIFI standard to review:\n\n{preprocessed_text}")
        ])
        self.prompt = self.prompt.partial(format_instructions=self.parser.get_format_instructions())

    def _should_request_knowledge(self, state: Dict[str, Any]) -> bool:
        if hasattr(self, "_output") and self._output.needs_knowledge:
            return True
        return False

    def _create_knowledge_request(self, state: Dict[str, Any]) -> KnowledgeRequest:
        issues = []
        if self._output.shariah_issues:
            issues.append(f"Shariah issues: {', '.join(self._output.shariah_issues)}")
        if self._output.clarity_issues:
            issues.append(f"Clarity issues: {', '.join(self._output.clarity_issues)}")
        if self._output.structure_issues:
            issues.append(f"Structure issues: {', '.join(self._output.structure_issues)}")

        return KnowledgeRequest(
            requester=self.name,
            query=self._output.knowledge_query or "",
            context=f"Reviewing AAOIFI standard. Issues identified: {'; '.join(issues)}",
            timestamp=None,
        )

    def _process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        formatted_prompt = self.prompt.format(preprocessed_text=state["preprocessed_text"])
        response = self.llm.invoke(formatted_prompt)

        try:
            self._output = self.parser.parse(response.content)
        except Exception as e:
            self.logger.error(f"Error parsing response: {e}")
            self.logger.error(f"Response content: {response.content}")
            self._output = ReviewerOutput(
                reviewed_text=state["preprocessed_text"],
                quality_score=0,
                notes=f"Error parsing response: {e}",
                shariah_issues=["Unable to review standard"],
                clarity_issues=[],
                structure_issues=[],
                needs_knowledge=False,
            )

        if self._should_request_knowledge(state):
            self.logger.info("Reviewer requesting knowledge")
            knowledge_request = self._create_knowledge_request(state)
            state["knowledge_request"] = knowledge_request
            state["knowledge_requests"].append(knowledge_request)
            return {
                "knowledge_request": knowledge_request,
                "quality_scores": {
                    **state["quality_scores"],
                    "reviewer": self._output.quality_score
                },
                "notes": self._output.notes
            }

        return {
            "reviewed_text": self._output.reviewed_text,
            "quality_scores": {
                **state["quality_scores"],
                "reviewer": self._output.quality_score
            },
            "notes": self._output.notes
        }
