"""Short-video production briefs; local templates are explicitly NOT AI."""
import json
import os
import re
import secrets
import urllib.request

import hosted_ai
from pydantic import BaseModel, Field


class Scene(BaseModel):
    start: int = Field(ge=0, le=180)
    end: int = Field(gt=0, le=180)
    visual: str = Field(min_length=1, max_length=1500)
    voiceover: str = Field(min_length=1, max_length=1500)
    caption: str = Field(min_length=1, max_length=300)


class VideoPackage(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=5000)
    script: str = Field(min_length=1, max_length=10000)
    scenes: list[Scene] = Field(min_length=4, max_length=5)
    captions: list[str] = Field(min_length=4, max_length=5)
    hashtags: list[str] = Field(min_length=1, max_length=12)


class ModelScene(BaseModel):
