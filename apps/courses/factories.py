from __future__ import annotations

import uuid

import factory
from factory.django import DjangoModelFactory

from apps.courses.models import ContentBlock, Course, CourseSection


class CourseFactory(DjangoModelFactory):
    class Meta:
        model = Course

    id = factory.LazyFunction(uuid.uuid4)
    instructor_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    instructor_fio = factory.Faker("name")
    discipline_name = "Информатика"
    education_direction = "09.03.01 Информатика и вычислительная техника"
    course_hours = 36
    status = Course.Status.DRAFT


class SectionFactory(DjangoModelFactory):
    class Meta:
        model = CourseSection

    id = factory.LazyFunction(uuid.uuid4)
    course = factory.SubFactory(CourseFactory)
    title = "Введение"
    description = "Базовые понятия"
    hours = 4
    objectives = factory.LazyFunction(lambda: ["Знать основы"])
    order = 0


class BlockFactory(DjangoModelFactory):
    class Meta:
        model = ContentBlock

    id = factory.LazyFunction(uuid.uuid4)
    section = factory.SubFactory(SectionFactory)
    type = ContentBlock.BlockType.THEORY
    content = factory.LazyFunction(lambda: {"text": "черновик"})
    source_meta = factory.LazyFunction(dict)
    version = 1
    order = 0
