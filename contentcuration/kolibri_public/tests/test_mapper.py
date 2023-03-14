import os
import tempfile

from django.core.management import call_command
from django.db import connections
from django.test import TestCase
from kolibri_content import models as kolibri_content_models
from kolibri_content.router import get_active_content_database
from kolibri_content.router import using_content_database
from kolibri_public import models as kolibri_public_models
from kolibri_public.tests.base import ChannelBuilder
from kolibri_public.utils.mapper import ChannelMapper

from contentcuration.models import Channel


class ChannelMapperTest(TestCase):

    @property
    def overrides(self):
        return {
        kolibri_public_models.ContentNode: {
            "available": True,
            "tree_id": self.mapper.tree_id,
        },
        kolibri_public_models.LocalFile: {
            "available": True,
        }
    }

    @classmethod
    def setUpClass(cls):
        super(ChannelMapperTest, cls).setUpClass()
        call_command("loadconstants")
        _, cls.tempdb = tempfile.mkstemp(suffix=".sqlite3")

        with using_content_database(cls.tempdb):
            call_command("migrate", "content", database=get_active_content_database(), no_input=True)
            builder = ChannelBuilder(models=kolibri_content_models)
            builder.insert_into_default_db()
            cls.source_root = kolibri_content_models.ContentNode.objects.get(id=builder.root_node["id"])
            cls.channel = kolibri_content_models.ChannelMetadata.objects.get(id=builder.channel["id"])
            contentcuration_channel = Channel.objects.create(id=cls.channel.id, name=cls.channel.name, public=True)
            contentcuration_channel.main_tree.published = True
            contentcuration_channel.main_tree.save()
            cls.mapper = ChannelMapper(cls.channel)
            cls.mapper.run()
            cls.mapped_root = cls.mapper.mapped_root

    def _assert_model(self, source, mapped, Model):
        for field in Model._meta.fields:
            column = field.column
            if hasattr(source, column):
                if Model in self.overrides and column in self.overrides[Model]:
                    self.assertEqual(self.overrides[Model][column], getattr(mapped, column))
                else:
                    self.assertEqual(getattr(source, column), getattr(mapped, column))

    def _assert_node(self, source, mapped):
        self._assert_model(source, mapped, kolibri_public_models.ContentNode)

        for src, mpd in zip(source.assessmentmetadata.all(), mapped.assessmentmetadata.all()):
            self._assert_model(src, mpd, kolibri_public_models.AssessmentMetaData)

        for src, mpd in zip(source.files.all(), mapped.files.all()):
            self._assert_model(src, mpd, kolibri_public_models.File)
            self._assert_model(src.local_file, mpd.local_file, kolibri_public_models.LocalFile)

    def _recurse_and_assert(self, sources, mappeds, recursion_depth=0):
        recursion_depths = []
        for source, mapped in zip(sources, mappeds):
            self._assert_node(source, mapped)
            source_children = source.children.all()
            mapped_children = mapped.children.all()
            self.assertEqual(len(source_children), len(mapped_children))
            recursion_depths.append(
                self._recurse_and_assert(
                    source_children,
                    mapped_children,
                    recursion_depth=recursion_depth + 1,
                )
            )
        return recursion_depth if not recursion_depths else max(recursion_depths)

    def test_map(self):
        with using_content_database(self.tempdb):
            self._recurse_and_assert([self.source_root], [self.mapped_root])
            self._assert_model(self.channel, self.mapper.mapped_channel, kolibri_public_models.ChannelMetadata)

    def test_map_replace(self):
        with using_content_database(self.tempdb):
            mapper = ChannelMapper(self.channel)
            mapper.run()
            self._recurse_and_assert([self.source_root], [mapper.mapped_root])
            self._assert_model(self.channel, self.mapper.mapped_channel, kolibri_public_models.ChannelMetadata)

    @classmethod
    def tearDownClass(cls):
        # Clean up datbase connection after the test
        connections[cls.tempdb].close()
        del connections.databases[cls.tempdb]
        super(ChannelMapperTest, cls).tearDownClass()
        if os.path.exists(cls.tempdb):
            os.remove(cls.tempdb)
