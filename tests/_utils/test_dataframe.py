from pandas import DataFrame

from pfdf._utils import dataframe


class TestTable:
    def test(_):
        fields = ("Label", "N", "Description", "ID")
        data = (
            ("Label A", "1", "Some data", "123"),
            ("Label B", "5", "Another row", "456"),
        )
        output = dataframe.table(data, fields[1:])

        assert isinstance(output, DataFrame)
        assert output.index.tolist() == ["Label A", "Label B"]
        assert output.columns.tolist() == ["N", "Description", "ID"]
        assert output["N"].tolist() == ["1", "5"]
        assert output["Description"].tolist() == ["Some data", "Another row"]
        assert output["ID"].tolist() == ["123", "456"]
