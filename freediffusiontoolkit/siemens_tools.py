from datetime import datetime
from pathlib import Path

import numpy as np

from .free_diffusion_tools import FreeDiffusionTool


class BasicSiemensTool(FreeDiffusionTool):
    def __init__(
        self,
        b_values: list | np.ndarray = np.array([0, 1000]),
        n_dims: int | None = 3,
        **kwargs,
    ):
        super().__init__(b_values, n_dims, **kwargs)

    def construct_header(
        self, filename: Path = None,
        n_dims: int = 3,
        b_values: list | np.ndarray | tuple = (0, 1000),
    ) -> list:
        """
        Create a header string for the diffusion vector file.

        Parameters
        n_dims: int
            Number of diffusion vector directions.
        b_values: list | np.ndarray
            An array containing the b values used for the diffusion vector file.
        kwargs: dict
            Options are explained in parent method documentation.
        """
        # This is the total number of applied dimensions
        n_directions = len(b_values) * n_dims

        head = list()
        head.append(
            r"# -----------------------------------------------------------------------------"
        )

        if filename is not None:
            if not isinstance(filename, Path):
                filename = Path(filename)
            filename = filename.name
        else:
            filename = "MyVectorSet.dvs"
        default_path = self.options.get(
            "default_path", r"C:\\Medcom\\MriCustomer\\seq\\DiffusionVectorSets\\"
        )
        head.append("# File: " + default_path + filename)

        now = datetime.now()
        current_time = now.strftime("%a %b %d %H:%M:%S %Y")
        head.append(f"# Date: {current_time}")

        description = self.options.get(
            "description", "Vector file for Siemens 'free' diffusion mode."
        )
        head.append(f"# Description: {description}")
        head.append(f"b-values: {b_values}")
        head.append(f"number dimensions: {n_dims}")
        comment = self.options.get("Comment", None)
        if comment:
            head.append(f"Comment: {comment}")

        head.append(
            r"# -----------------------------------------------------------------------------"
        )
        head.append(f"[directions={n_directions}]")

        coordinate_system = self.options.get("CoordinateSystem", "xyz")
        head.append(f"CoordinateSystem = {coordinate_system}")

        normalisation = self.options.get("Normalisation", "none")
        head.append(f"Normalisation = {normalisation}")
        # NOTE: There is an option to add a comment here. "comment = example text"
        return head

    def save(self, filename: Path = "") -> None:
        """
        Write vector file for Siemens.

        Supports VE11c but might support other software version.
        Recommended file suffix is .dvs

        Parameters
        filename: Path
            Pathlib Path to the diffusion vector file.

        options: dict
            Several options to modify the header information.
                Description: str
                    Description of the diffusion vector file.
                CoordinateSystem: str = "xyz"
                    Coordinate System used by the scaner (?)
                Normalisation: str = "maximum", "none"
                    Normalisation mode used by the scaner (?)
                Comment: str
                    Further information and comments about the diffusion vector file.
                Newline: str = "\n", "\r\n" for legacy

        """
        header = self.construct_header(filename=filename)

        # get diffusion values
        diffusion_vectors = self.get_diffusion_vectors()

        self.write(filename, header, diffusion_vectors)

    def write(
        self, filename: Path, header: list, diffusion_vectors: list | np.ndarray
    ) -> None:
        with filename.open("w") as file:
            # write header to file
            for line in header:
                file.write(line + self.options.get("newline", "\n"))

            # write values to file
            for row_idx, row in enumerate(diffusion_vectors):
                file.write(
                    self.vector_to_string(row_idx, row)
                    + self.options.get("newline", "\n")
                )

    @staticmethod
    def vector_to_string(
        index: int, vector: np.ndarray | list, decimals: int = 6
    ) -> str:
        """Siemens style vector conversion."""
        return (
            f"Vector[{index}] = ("
            f"{vector[0]: .{decimals}f},"
            f"{vector[1]: .{decimals}f},"
            f"{vector[2]: .{decimals}f})"
        )


class LegacySiemensTool(BasicSiemensTool):
    def __init__(self, b_values: list | np.ndarray, n_dims: int, **kwargs):
        super().__init__(b_values, n_dims, **kwargs)
        self.options["newline"] = "\r\n"
        self.options["default_path"] = r"C:\\Medcom\\MriCustomer\\seq\\"

    def save(self, filename: Path = Path("DiffusionVectors.txt"), **options: dict):
        """
        Write vector file for Siemens (legacy).

        Supports VB17c but might support other software version.
        Filename should be DiffusionVectors.txt since this is the supported filename.

        Parameters
        filename: Path
            Pathlib Path to the diffusion vector file.

        options: dict
            Several options to modify the header information.
                Description: str
                    Description of the diffusion vector file.
                CoordinateSystem: str = "xyz"
                    Coordinate System used by the scaner (?)
                Normalisation: str = "maximum", "none"
                    Normalisation mode used by the scaner (?)
                Comment: str
                    Further information and comments about the diffusion vector file.
                Newline: str = "\r\n" for legacy

        """
        header = self.construct_header(filename=filename)
        for idx, head in enumerate(header):
            if head.startswith("[directions="):
                header[idx] = head.replace("[directions=", "")

        diffusion_vectors = self.get_diffusion_vectors()

        self.write(filename, header, diffusion_vectors)