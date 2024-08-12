from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import expression
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.types import DateTime


class time_bucket_gapfill(FunctionElement):
    name = "time_bucket_gapfill"


@compiles(time_bucket_gapfill)
def compile_time_bucket_gapfill(element, compiler, **kw):
    if len(element.clauses) < 2:
        raise ValueError("time_bucket_gapfill requires at least 2 arguments")
    return "time_bucket_gapfill({})".format(", ".join(compiler.process(arg) for arg in element.clauses))


class date_part(expression.FunctionElement):
    type = DateTime()
    name = "date_part"


@compiles(date_part)
def compile_date_part(element, compiler, **kw):
    if len(element.clauses) != 2:
        raise ValueError("date_part requires exactly two arguments")
    return f"date_part({compiler.process(element.clauses[0])}, {compiler.process(element.clauses[1])})"


class date_trunc(expression.FunctionElement):
    type = DateTime()
    name = "date_trunc"


@compiles(date_trunc)
def compile_date_trunc(element, compiler, **kw):
    if len(element.clauses) != 2:
        raise ValueError("date_trunc requires exactly two arguments")
    return f"date_trunc({compiler.process(element.clauses[0])}, {compiler.process(element.clauses[1])})"
