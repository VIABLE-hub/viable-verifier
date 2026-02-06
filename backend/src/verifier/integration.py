"""
Integration-Modul für den Verifier.

Enthält Hilfsfunktionen, die verschiedene Module des Verifiers verbinden und
robuste Fehlerbehandlung sicherstellen.
"""

from logging import getLogger
import traceback
from .validators import check_presentation_integrity
from .bbs_verification import verify_bbs_proof
from .field_extractor import get_field_value, extract_presentation_from_vp
from .utils import process_oversized_fields
from .constants import FIELD_MAPPINGS

logger = getLogger("LOGGER")


def safe_verify_presentation(
    decoded_vp, presentation_definition, raw_token=None
):
    """
    Führt eine robuste Verifikation einer Präsentation durch,
    mit umfassender Fehlerbehandlung und Debugging

    Args:
        decoded_vp: Das dekodierte VP-Objekt
        presentation_definition: Die Präsentationsdefinition mit Pflichtfeldern
        raw_token: Das rohe Token (für SD-JWT erforderlich)

    Returns:
        (bool, dict): (Erfolgsstatus, Details der Verifikation)
    """
    try:
        verification_steps = {
            "integrity": {"status": "pending", "message": ""},
            "bbs_verification": {"status": "pending", "message": ""},
            "field_normalization": {"status": "pending", "message": ""},
            "oversized_fields": {"status": "pending", "message": ""},
        }

        # Detect SD-JWT
        is_sd_jwt = raw_token and "~" in raw_token

        # Extrahiere die Präsentation (nur für BBS+)
        if not is_sd_jwt:
            presentation = extract_presentation_from_vp(decoded_vp)

        # SCHRITT 1: Präsentationsintegrität prüfen
        # Für SD-JWT verschieben wir dies nach die Signaturprüfung, da wir den Payload erst dann haben
        if not is_sd_jwt:
            try:
                integrity_valid, integrity_msg = check_presentation_integrity(
                    decoded_vp, presentation_definition
                )
                if integrity_valid:
                    verification_steps["integrity"] = {
                        "status": "success",
                        "message": "Präsentationsintegrität erfolgreich geprüft",
                    }
                else:
                    verification_steps["integrity"] = {
                        "status": "error",
                        "message": f"Präsentationsintegritätsprüfung fehlgeschlagen: {integrity_msg}",
                    }
                    return False, {
                        "steps": verification_steps,
                        "error": integrity_msg,
                        "error_type": "presentation_integrity_error",
                    }
            except Exception as e:
                verification_steps["integrity"] = {
                    "status": "error",
                    "message": f"Fehler bei der Integritätsprüfung: {str(e)}",
                }
                logger.error(f"Exception in integrity check: {traceback.format_exc()}")
                return False, {
                    "steps": verification_steps,
                    "error": f"Fehler bei der Integritätsprüfung: {str(e)}",
                    "error_type": "integrity_check_exception",
                }
        else:
            verification_steps["integrity"] = {
                "status": "pending",
                "message": "Warte auf SD-JWT Payload...",
            }

        # SCHRITT 2: Verarbeite übergroße Felder (wie Base64-Bilder)
        # Nur für BBS relevant bzw. wenn strukturierte Daten vorliegen
        if not is_sd_jwt:
            try:
                # Hole die offengelegten Werte
                vc = decoded_vp.get("verifiable_credential", {})
                if "values" in vc:
                    # Verarbeite übergroße Felder in den Werten
                    vc["values"] = process_oversized_fields(vc["values"])
                    verification_steps["oversized_fields"] = {
                        "status": "success",
                        "message": f"Übergroße Felder verarbeitet: {len(vc['values'])} Felder geprüft",
                    }
                else:
                    verification_steps["oversized_fields"] = {
                        "status": "warning",
                        "message": "Keine übergroßen Felder gefunden oder keine Werte vorhanden",
                    }
            except Exception as e:
                verification_steps["oversized_fields"] = {
                    "status": "warning",
                    "message": f"Fehler bei der Verarbeitung übergroßer Felder: {str(e)}",
                }
                logger.warning(f"Exception in oversized field processing: {str(e)}")
                # Wir brechen hier nicht ab, da dies nur eine Optimierung ist

        # SCHRITT 3: Führe die kryptographische Verifikation durch
        try:
            if is_sd_jwt:
                from .sd_jwt_verification import verify_sd_jwt_presentation

                # Adjusted to receive payload
                sd_valid, sd_msg, sd_payload = verify_sd_jwt_presentation(
                    raw_token
                )

                if sd_valid:
                    verification_steps["bbs_verification"] = {
                        "status": "success",
                        "message": "SD-JWT Signatur (ECDSA) erfolgreich verifiziert",
                    }

                    # JETZT: Integritätsprüfung für SD-JWT ("Delayed Step 1")
                    # Wir müssen eine synthetische Struktur schaffen, damit die Validatoren funktionieren
                    # SD-JWT Payload entspricht i.d.R. den Claims.
                    # Wir wrappen es in eine Struktur, die 'values' oder 'credentialSubject' imitiert,
                    # je nachdem wie check_presentation_integrity sucht.

                    # Construct synthetic VP for validation
                    # Note: check_presentation_integrity looks in 'verifiable_credential.values' OR top-level fields
                    synthetic_vp = {
                        "verifiable_credential": {
                            "values": sd_payload,
                            "credentialSubject": sd_payload,
                        }
                    }
                    # Merge top-level claims too just in case
                    synthetic_vp.update(sd_payload)

                    # Modifiziere die Definition: Entferne technische BBS-Felder
                    sd_def = presentation_definition.copy()
                    sd_def["technical_fields"] = []  # Keine BBS Felder für SD-JWT

                    try:
                        int_valid, int_msg = check_presentation_integrity(
                            synthetic_vp, sd_def
                        )
                        if int_valid:
                            verification_steps["integrity"] = {
                                "status": "success",
                                "message": "SD-JWT Claims erfolgreich validiert",
                            }
                            # Update decoded_vp to be the synthetic one for Step 4
                            decoded_vp = synthetic_vp
                        else:
                            verification_steps["integrity"] = {
                                "status": "error",
                                "message": f"SD-JWT Claims unvollständig: {int_msg}",
                            }
                            return False, {
                                "steps": verification_steps,
                                "error": int_msg,
                                "error_type": "presentation_integrity_error",
                            }
                    except Exception as e:
                        return False, {
                            "steps": verification_steps,
                            "error": f"Fehler bei SD-JWT Integrity Check: {e}",
                            "error_type": "integrity_check_exception",
                        }

                    # Return success with payload
                    return True, {
                        "steps": verification_steps,
                        "message": "Verifikation erfolgreich abgeschlossen",
                        "verified_payload": sd_payload,
                        "format": "sd_jwt",
                    }

                else:
                    verification_steps["bbs_verification"] = {
                        "status": "error",
                        "message": f"SD-JWT Signaturprüfung fehlgeschlagen: {sd_msg}",
                    }
                    return False, {
                        "steps": verification_steps,
                        "error": sd_msg,
                        "error_type": "sd_jwt_verification_failed",
                    }
            else:
                bbs_valid, bbs_msg = verify_bbs_proof(decoded_vp)
                if bbs_valid:
                    verification_steps["bbs_verification"] = {
                        "status": "success",
                        "message": "BBS+ Signaturprüfung erfolgreich",
                    }
                else:
                    verification_steps["bbs_verification"] = {
                        "status": "error",
                        "message": f"BBS+ Signaturprüfung fehlgeschlagen: {bbs_msg}",
                    }
                    return False, {
                        "steps": verification_steps,
                        "error": bbs_msg,
                        "error_type": "bbs_verification_failed",
                    }
        except Exception as e:
            verification_steps["bbs_verification"] = {
                "status": "error",
                "message": f"Fehler bei der Verifikation: {str(e)}",
            }
            logger.error(f"Exception in verification: {traceback.format_exc()}")
            return False, {
                "steps": verification_steps,
                "error": f"Fehler bei der Verifikation: {str(e)}",
                "error_type": "verification_exception",
            }

        # SCHRITT 4: Feldnormalisierung und Mapping-Prüfung
        try:
            # Prüfe, ob alle gemappten Felder korrekt extrahiert werden können
            field_issues = []
            for original_field, mapped_field in FIELD_MAPPINGS.items():
                original_value = get_field_value(decoded_vp, original_field)
                mapped_value = get_field_value(decoded_vp, mapped_field)

                # Wenn das Originalfeld vorhanden ist, sollte auch das gemappte Feld auffindbar sein
                if original_value is not None and mapped_value is None:
                    field_issues.append(
                        f"'{original_field}' gefunden, aber '{mapped_field}' fehlt"
                    )
                elif original_value is None and mapped_value is not None:
                    field_issues.append(
                        f"'{mapped_field}' gefunden, aber '{original_field}' fehlt"
                    )
                # Wenn beide vorhanden sind, sollten sie übereinstimmen
                elif (
                    original_value is not None
                    and mapped_value is not None
                    and str(original_value) != str(mapped_value)
                ):
                    field_issues.append(
                        f"'{original_field}' und '{mapped_field}' haben unterschiedliche Werte"
                    )

            if field_issues:
                verification_steps["field_normalization"] = {
                    "status": "warning",
                    "message": f"Probleme mit Feld-Mapping gefunden: {', '.join(field_issues)}",
                    "issues": field_issues,
                }
            else:
                verification_steps["field_normalization"] = {
                    "status": "success",
                    "message": "Alle Felder wurden korrekt normalisiert",
                }
        except Exception as e:
            verification_steps["field_normalization"] = {
                "status": "warning",
                "message": f"Fehler bei der Feldnormalisierung: {str(e)}",
            }
            logger.warning(f"Exception in field normalization: {str(e)}")
            # Wir brechen hier nicht ab, da dies nur eine Diagnose ist

        # Alle Schritte erfolgreich abgeschlossen
        return True, {
            "steps": verification_steps,
            "message": "Verifikation erfolgreich abgeschlossen",
        }

    except Exception as e:
        logger.error(
            f"Unerwarteter Fehler bei der Verifikation: {traceback.format_exc()}"
        )
        return False, {
            "error": f"Unerwarteter Fehler bei der Verifikation: {str(e)}",
            "error_type": "unexpected_verification_error",
            "traceback": traceback.format_exc(),
        }
