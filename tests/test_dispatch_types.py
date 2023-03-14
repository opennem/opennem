from opennem.core.dispatch_type import DispatchType, parse_dispatch_type


class TestDispatchType:
    def test_none(self):
        subject = parse_dispatch_type(None)

        assert subject is None, "No dispatch type is none"

    def test_generating(self):
        subject = parse_dispatch_type("generating")

        assert subject is DispatchType.GENERATOR, "Generating is generator"

    def test_generator(self):
        subject = parse_dispatch_type("Generator")

        assert subject is DispatchType.GENERATOR, "Generator is generator"

    def test_load(self):
        subject = parse_dispatch_type("load")

        assert subject is DispatchType.LOAD, "Load is loading"

    def test_generating_padded(self):
        subject = parse_dispatch_type("  generating  ")

        assert subject is DispatchType.GENERATOR, "Generating padded is generating"

    def test_generating_case(self):
        subject = parse_dispatch_type("GeNeRaTiNg")

        assert subject is DispatchType.GENERATOR, "Generating case is generator"
