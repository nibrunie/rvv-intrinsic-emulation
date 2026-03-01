"""Unit tests for LMULType.is_valid_for_eew"""

import pytest
from rie_generator.core import EltType, LMULType


# All standard LMUL values and 8/16/32/64-bit element types for convenience.
ALL_LMULS = [
    LMULType.MF8,
    LMULType.MF4,
    LMULType.MF2,
    LMULType.M1,
    LMULType.M2,
    LMULType.M4,
    LMULType.M8,
]

EEW8_TYPES = [EltType.U8, EltType.S8]
EEW16_TYPES = [EltType.U16, EltType.S16]
EEW32_TYPES = [EltType.U32, EltType.S32]
EEW64_TYPES = [EltType.U64, EltType.S64]


class TestIsValidForEew:
    """Tests for LMULType.is_valid_for_eew."""

    # ------------------------------------------------------------------
    # EEW = 8: every LMUL should be valid (LMUL/1 >= 1/8 for all LMUL)
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("elt_type", EEW8_TYPES)
    @pytest.mark.parametrize("lmul", ALL_LMULS)
    def test_eew8_all_lmuls_valid(self, elt_type, lmul):
        assert LMULType.is_valid_for_eew(elt_type, lmul) is True

    # ------------------------------------------------------------------
    # EEW = 16: MF8 is invalid (LMUL=1/8 / 2 = 1/16 < 1/8)
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("elt_type", EEW16_TYPES)
    def test_eew16_mf8_invalid(self, elt_type):
        assert LMULType.is_valid_for_eew(elt_type, LMULType.MF8) is False

    @pytest.mark.parametrize("elt_type", EEW16_TYPES)
    @pytest.mark.parametrize(
        "lmul",
        [LMULType.MF4, LMULType.MF2, LMULType.M1, LMULType.M2, LMULType.M4, LMULType.M8],
    )
    def test_eew16_valid_lmuls(self, elt_type, lmul):
        assert LMULType.is_valid_for_eew(elt_type, lmul) is True

    # ------------------------------------------------------------------
    # EEW = 32: MF8 and MF4 are invalid
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("elt_type", EEW32_TYPES)
    @pytest.mark.parametrize("lmul", [LMULType.MF8, LMULType.MF4])
    def test_eew32_invalid_lmuls(self, elt_type, lmul):
        assert LMULType.is_valid_for_eew(elt_type, lmul) is False

    @pytest.mark.parametrize("elt_type", EEW32_TYPES)
    @pytest.mark.parametrize(
        "lmul",
        [LMULType.MF2, LMULType.M1, LMULType.M2, LMULType.M4, LMULType.M8],
    )
    def test_eew32_valid_lmuls(self, elt_type, lmul):
        assert LMULType.is_valid_for_eew(elt_type, lmul) is True

    # ------------------------------------------------------------------
    # EEW = 64: MF8, MF4, and MF2 are invalid
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("elt_type", EEW64_TYPES)
    @pytest.mark.parametrize("lmul", [LMULType.MF8, LMULType.MF4, LMULType.MF2])
    def test_eew64_invalid_lmuls(self, elt_type, lmul):
        assert LMULType.is_valid_for_eew(elt_type, lmul) is False

    @pytest.mark.parametrize("elt_type", EEW64_TYPES)
    @pytest.mark.parametrize(
        "lmul",
        [LMULType.M1, LMULType.M2, LMULType.M4, LMULType.M8],
    )
    def test_eew64_valid_lmuls(self, elt_type, lmul):
        assert LMULType.is_valid_for_eew(elt_type, lmul) is True

    # ------------------------------------------------------------------
    # Signed vs unsigned should behave identically for the same width
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "unsigned,signed",
        [
            (EltType.U8, EltType.S8),
            (EltType.U16, EltType.S16),
            (EltType.U32, EltType.S32),
            (EltType.U64, EltType.S64),
        ],
    )
    @pytest.mark.parametrize("lmul", ALL_LMULS)
    def test_signed_unsigned_symmetry(self, unsigned, signed, lmul):
        assert LMULType.is_valid_for_eew(unsigned, lmul) == LMULType.is_valid_for_eew(
            signed, lmul
        )
