from .provider_test import ProviderTest
from gunpowder import *
import numpy as np
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class UpSampleTestSource(BatchProvider):

    def setup(self):

        self.provides(
            ArrayKeys.RAW,
            ArraySpec(
                roi=Roi((0, 0, 0), (1000, 1000, 1000)),
                voxel_size=(4, 4, 4)))

        self.provides(
            ArrayKeys.GT_LABELS,
            ArraySpec(
                roi=Roi((0, 0, 0), (1000, 1000, 1000)),
                voxel_size=(4, 4, 4)))

    def provide(self, request):

        batch = Batch()

        # have the pixels encode their position
        for (array_key, spec) in request.array_specs.items():

            roi = spec.roi

            for d in range(3):
                assert roi.get_begin()[d]%4 == 0, "roi %s does not align with voxels"

            data_roi = roi/4

            # the z,y,x coordinates of the ROI
            meshgrids = np.meshgrid(
                    range(data_roi.get_begin()[0], data_roi.get_end()[0]),
                    range(data_roi.get_begin()[1], data_roi.get_end()[1]),
                    range(data_roi.get_begin()[2], data_roi.get_end()[2]), indexing='ij')
            data = meshgrids[0] + meshgrids[1] + meshgrids[2]
            spec = self.spec[array_key].copy()
            spec.roi = roi
            batch.arrays[array_key] = Array(
                    data,
                    spec)
        return batch

class TestUpSample(ProviderTest):

    def test_output(self):

        source = UpSampleTestSource()

        ArrayKey('RAW_UPSAMPLED')
        ArrayKey('GT_LABELS_UPSAMPLED')

        request = BatchRequest()
        request.add(ArrayKeys.RAW, (200,200,200))
        request.add(ArrayKeys.RAW_UPSAMPLED, (120,120,120))
        request.add(ArrayKeys.GT_LABELS, (200,200,200))
        request.add(ArrayKeys.GT_LABELS_UPSAMPLED, (200,200,200))

        pipeline = (
                UpSampleTestSource() +
                UpSample(ArrayKeys.RAW, 2, ArrayKeys.RAW_UPSAMPLED) +
                UpSample(ArrayKeys.GT_LABELS, 2, ArrayKeys.GT_LABELS_UPSAMPLED)
        )

        with build(pipeline):
            batch = pipeline.request_batch(request)

        for (array_key, array) in batch.arrays.items():

            # assert that pixels encode their position for supposedly unaltered
            # arrays
            if array_key in [ArrayKeys.RAW, ArrayKeys.GT_LABELS]:

                # the z,y,x coordinates of the ROI
                roi = array.spec.roi/4
                meshgrids = np.meshgrid(
                        range(roi.get_begin()[0], roi.get_end()[0]),
                        range(roi.get_begin()[1], roi.get_end()[1]),
                        range(roi.get_begin()[2], roi.get_end()[2]), indexing='ij')
                data = meshgrids[0] + meshgrids[1] + meshgrids[2]

                self.assertTrue(np.array_equal(array.data, data), str(array_key))

            elif array_key == ArrayKeys.RAW_UPSAMPLED:
                self.assertEqual(array.data[0,0,0], 30)
                self.assertEqual(array.data[1,0,0], 30)
                self.assertEqual(array.data[2,0,0], 31)
                self.assertEqual(array.data[3,0,0], 31)

            elif array_key == ArrayKeys.GT_LABELS_UPSAMPLED:

                self.assertEqual(array.data[0,0,0], 0)
                self.assertEqual(array.data[1,0,0], 0)
                self.assertEqual(array.data[2,0,0], 1)
                self.assertEqual(array.data[3,0,0], 1)

            else:

                self.assertTrue(False, "unexpected array type")

    def test_crop(self):

        ArrayKey('RAW_UPSAMPLED')
        ArrayKey('GT_LABELS_UPSAMPLED')

        request = BatchRequest()
        request.add(ArrayKeys.RAW_UPSAMPLED, (116,120,120))
        request.add(ArrayKeys.GT_LABELS, (200,200,200))
        request.add(ArrayKeys.GT_LABELS_UPSAMPLED, (196,196,196))

        pipeline = (
                UpSampleTestSource() +
                UpSample(ArrayKeys.RAW, 2, ArrayKeys.RAW_UPSAMPLED) +
                UpSample(ArrayKeys.GT_LABELS, 2, ArrayKeys.GT_LABELS_UPSAMPLED)
        )

        with build(pipeline):
            batch = pipeline.request_batch(request)

        for (array_key, array) in batch.arrays.items():
            for dim, data_length in enumerate(array.data.shape):
                roi_dim = array.spec.roi.get_shape()[dim]
                voxel_size_dim = array.spec.voxel_size[dim]
                self.assertEqual(data_length, roi_dim / voxel_size_dim)
            # assert that pixels encode their position for supposedly unaltered
            # arrays
            if array_key in [ArrayKeys.RAW, ArrayKeys.GT_LABELS]:
                continue
                # the z,y,x coordinates of the ROI
                roi = array.spec.roi/4
                meshgrids = np.meshgrid(
                        range(roi.get_begin()[0], roi.get_end()[0]),
                        range(roi.get_begin()[1], roi.get_end()[1]),
                        range(roi.get_begin()[2], roi.get_end()[2]), indexing='ij')
                data = meshgrids[0] + meshgrids[1] + meshgrids[2]

                self.assertTrue(np.array_equal(array.data, data), str(array_key))

            elif array_key == ArrayKeys.RAW_UPSAMPLED:
                self.assertEqual(array.data[0,0,0], 30)
                self.assertEqual(array.data[1,0,0], 31)
                self.assertEqual(array.data[2,0,0], 31)
                self.assertEqual(array.data[3,0,0], 32)

            elif array_key == ArrayKeys.GT_LABELS_UPSAMPLED:
                self.assertEqual(array.data[0,0,0], 0)
                self.assertEqual(array.data[1,0,0], 1)
                self.assertEqual(array.data[2,0,0], 1)
                self.assertEqual(array.data[3,0,0], 2)

            else:

                self.assertTrue(False, "unexpected array type")

    def test_crop_invalid_roi(self):

        source = UpSampleTestSource()

        ArrayKey('RAW_UPSAMPLED')
        ArrayKey('GT_LABELS_UPSAMPLED')

        request = BatchRequest()
        request.add(ArrayKeys.RAW_UPSAMPLED, (118,120,120))
        request.add(ArrayKeys.GT_LABELS, (200,200,200))
        request.add(ArrayKeys.GT_LABELS_UPSAMPLED, (196,196,196))

        pipeline = (
                UpSampleTestSource() +
                UpSample(ArrayKeys.RAW, 2, ArrayKeys.RAW_UPSAMPLED) +
                UpSample(ArrayKeys.GT_LABELS, 2, ArrayKeys.GT_LABELS_UPSAMPLED)
        )

        with build(pipeline):
            with self.assertRaises(AssertionError):
                pipeline.request_batch(request)
