from unittest import mock
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import null
from opennem.exporter.r2_bucket import OpennemDataSetSerialize, write_content_to_r2, write_stat_set_to_r2
from opennem.api.stats.schema import OpennemDataSet, load_opennem_dataset_from_file
from opennem import settings
from opennem.utils.tests import TEST_FIXTURE_PATH

class TestR2Bucket:

    @pytest.mark.asyncio
    async def test_write_stat_set_to_r2(self):
        power=load_opennem_dataset_from_file(TEST_FIXTURE_PATH / f"nem_nsw1_7d.json")
        
        with patch.object(settings, 's3_endpoint_url', 'https://17399e149aeaa08c0c7bbb15382fa5c3.r2.cloudflarestorage.com'):
            with patch.object(settings, 's3_bucket_name', 'r2-dev'):
                save_response = await write_stat_set_to_r2(power, '/test.json')
        
        assert save_response is not None
        assert isinstance(save_response, int)

    @pytest.mark.asyncio
    async def test_write_content_to_r2(self):
        file = open(TEST_FIXTURE_PATH / f"test.txt", 'r')
        
        with patch.object(settings, 's3_endpoint_url', 'https://17399e149aeaa08c0c7bbb15382fa5c3.r2.cloudflarestorage.com'):
            with patch.object(settings, 's3_bucket_name', 'r2-dev'):
                save_response = await write_content_to_r2(file.read(), '/test.txt')
        
        assert save_response is not None
        assert isinstance(save_response, int) 