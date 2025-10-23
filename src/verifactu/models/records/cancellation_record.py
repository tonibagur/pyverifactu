"""Cancellation record model"""

from __future__ import annotations

import hashlib
from pydantic import Field, model_validator

from verifactu.models.records.record import Record


class CancellationRecord(Record):
    """
    Cancellation record (invoice cancellation)

    Registro de anulación de una factura

    @field RegistroAnulacion
    """

    # Indicador que especifica que se trata de la anulación de un registro que no existe en la
    # AEAT o en el SIF.
    # @field SinRegistroPrevio
    without_prior_record: bool = Field(
        False, description="Indicates cancellation of a non-existing record"
    )

    @model_validator(mode="after")
    def validate_enforce_previous_invoice(self) -> "CancellationRecord":
        """Validate previous invoice is always required for cancellation records"""
        if self.previous_invoice_id is None:
            raise ValueError("Previous invoice ID is required for all cancellation records")
        if self.previous_hash is None:
            raise ValueError("Previous hash is required for all cancellation records")
        return self

    def calculate_hash(self) -> str:
        """
        Calculate record hash

        Returns:
            Expected record hash (64 uppercase hex characters)
        """
        # Format datetime without microseconds (same format as XML)
        # Use local timezone like PHP does with format('c')
        import time

        dt = self.hashed_at

        # If no timezone info, add local timezone (like PHP does)
        if dt.tzinfo is None:
            # Get local timezone offset
            if time.daylight and time.localtime().tm_isdst:
                # Daylight saving time is in effect
                offset_seconds = -time.altzone
            else:
                # Standard time
                offset_seconds = -time.timezone

            from datetime import timezone, timedelta
            local_tz = timezone(timedelta(seconds=offset_seconds))
            dt = dt.replace(tzinfo=local_tz)

        # Format: YYYY-MM-DDTHH:MM:SS+HH:MM (no microseconds!)
        dt_str = dt.strftime('%Y-%m-%dT%H:%M:%S')

        # Add timezone offset in format +HH:MM
        offset = dt.utcoffset()
        if offset is not None:
            total_seconds = int(offset.total_seconds())
            hours, remainder = divmod(abs(total_seconds), 3600)
            minutes = remainder // 60
            sign = '+' if total_seconds >= 0 else '-'
            dt_str += f'{sign}{hours:02d}:{minutes:02d}'
        else:
            dt_str += '+00:00'

        # NOTE: Values should NOT be escaped as that what the AEAT says ¯\_(ツ)_/¯
        payload = (
            f"IDEmisorFacturaAnulada={self.invoice_id.issuer_id}"
            f"&NumSerieFacturaAnulada={self.invoice_id.invoice_number}"
            f"&FechaExpedicionFacturaAnulada={self.invoice_id.issue_date.strftime('%d-%m-%Y')}"
            f"&Huella={self.previous_hash or ''}"
            f"&FechaHoraHusoGenRegistro={dt_str}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()

    def get_record_element_name(self) -> str:
        """Get record element name for XML export"""
        return "RegistroAnulacion"

    def export_custom_properties(self, record_element: any) -> None:
        """Export custom record properties to XML"""
        # Implementation would go here for XML export
        # This requires an XML library which we'll implement when needed
        pass
