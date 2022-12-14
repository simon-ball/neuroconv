from abc import abstractmethod

from typing import Dict, Optional

import numpy as np
import pandas as pd
from pynwb import NWBFile
from pynwb.epoch import TimeIntervals

from ...basedatainterface import BaseDataInterface
from ...utils.types import FilePathType
from ...tools.nwb_helpers import make_or_load_nwbfile


def convert_df_to_time_intervals(
    df: pd.DataFrame,
    name: str = "trials",
    description: Optional[str] = None,
    column_name_mapping: Dict[str, str] = None,
    column_descriptions: Dict[str, str] = None,
):
    if column_name_mapping is not None:
        df.rename(columns=column_name_mapping, inplace=True)
    if description is None:
        description = name
    time_intervals = TimeIntervals(name, description)
    if "start_time" not in df:
        raise ValueError(f"df must contain a column named 'start_time'. Existing columns: {df.columns.to_list()}")
    if "stop_time" not in df:
        df["stop_time"] = np.r_[df["start_time"][1:].to_numpy(), np.nan]
    for col in df:
        if col not in ("start_time", "stop_time"):
            time_intervals.add_column(col, column_descriptions.get(col, col))
    for i, row in df.iterrows():
        time_intervals.add_row(row.to_dict())

    return time_intervals


class TimeIntervalsInterface(BaseDataInterface):
    def __init__(
        self,
        file_path: FilePathType,
        read_kwargs: Optional[dict] = None,
        verbose: bool = True,
    ):
        read_kwargs = read_kwargs or dict()
        super().__init__(file_path=file_path)
        self.verbose = verbose

        self.df = self._read_file(file_path, **read_kwargs)

    def get_metadata(self):
        return dict(
            TimeIntervals=dict(
                trials=dict(
                    name="trials",
                    description="trials",
                )
            )
        )

    def get_metadata_schema(self):
        pass  # todo

    def run_conversion(
        self,
        nwbfile_path: Optional[str] = None,
        nwbfile: Optional[NWBFile] = None,
        metadata: Optional[dict] = None,
        overwrite: bool = False,
        tag="trials",
        **conversion_options,
    ):
        with make_or_load_nwbfile(
            nwbfile_path=nwbfile_path, nwbfile=nwbfile, metadata=metadata, overwrite=overwrite, verbose=self.verbose
        ) as nwbfile_out:
            self.time_intervals = convert_df_to_time_intervals(self.df, **metadata["TimeIntervals"][tag])
            nwbfile_out.add_time_intervals(self.time_intervals)

        return nwbfile_out

    @abstractmethod
    def _read_file(self, file_path: FilePathType, **read_kwargs):
        pass
