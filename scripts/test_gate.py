#!/usr/bin/env python3
"""Tests for the noise gate. Run: python3 scripts/test_gate.py"""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import gate


def item(text, subject="", sender="alguien@kavak.com", recipients=None):
    return {"subject": subject, "text": text, "sender": sender,
            "recipients": recipients or ["armando.flores@driverdo.com"]}


class ExploratoryNeverBecomesATask(unittest.TestCase):
    def test_hedged_commitment_is_rejected(self):
        for t in [
            "Tal vez te mando la cotización el viernes, lo estoy viendo.",
            "Podríamos preparar una propuesta para Kavak la semana que entra.",
            "Maybe I'll send the pricing on Friday.",
            "Estaría bien que revisemos las tarifas en algún momento.",
            "What if we prepare a deck for the RFP?",
        ]:
            v = gate.evaluate(item(t))
            self.assertFalse(v["accept"], t)
            self.assertEqual(v["reason"], "exploratorio", t)

    def test_firm_commitment_survives_a_hedge_elsewhere(self):
        # Hedging in one sentence must not veto a firm commitment in another.
        v = gate.evaluate(item("Tal vez luego veamos lo del piloto. "
                               "Te mando la cotización de Kavak el viernes."))
        self.assertTrue(v["accept"])


class CommentaryAboutTasksNeverBecomesATask(unittest.TestCase):
    def test_meta_is_rejected(self):
        for t in [
            "Ya actualicé la lista de pendientes, te mando el resumen.",
            "El status de la tarea T-4 sigue abierto, voy a revisarlo.",
            "Según el brief de hoy, necesito que confirmes la tarifa.",
            "Recordatorio automático: te mando el reporte.",
            "Closed the ticket; I'll send the summary.",
        ]:
            v = gate.evaluate(item(t))
            self.assertFalse(v["accept"], t)
            self.assertEqual(v["reason"], "meta", t)


class OnlyExplicitCommitments(unittest.TestCase):
    def test_plain_chatter_is_rejected(self):
        for t in ["Gracias, quedo atento.", "Buenos días equipo, feliz miércoles.",
                  "FYI, adjunto el reporte de agosto.", "Excelente trabajo ayer."]:
            v = gate.evaluate(item(t))
            self.assertFalse(v["accept"], t)
            self.assertEqual(v["reason"], "sin_compromiso", t)

    def test_real_commitments_accepted(self):
        v = gate.evaluate(item("Te mando la cotización de Kavak antes del 5.",
                               subject="Cotización Kavak"))
        self.assertTrue(v["accept"])
        self.assertEqual(v["action"], "enviar")
        self.assertEqual(v["counterparty"], "kavak")
        self.assertEqual(v["domain"], "operacion-kavak")


class DedupeAtCreation(unittest.TestCase):
    def test_same_action_same_counterparty_suppressed(self):
        open_tasks = [{"status": "open", "archived": False, "code": "T-7",
                       "action": "enviar", "counterparty": "kavak"}]
        self.assertEqual(gate.is_duplicate("enviar", "kavak", open_tasks), "T-7")

    def test_same_action_other_counterparty_passes(self):
        open_tasks = [{"status": "open", "archived": False, "code": "T-7",
                       "action": "enviar", "counterparty": "kavak"}]
        self.assertEqual(gate.is_duplicate("enviar", "clicars", open_tasks), "")

    def test_closed_task_does_not_block(self):
        open_tasks = [{"status": "done", "archived": False, "code": "T-7",
                       "action": "enviar", "counterparty": "kavak"}]
        self.assertEqual(gate.is_duplicate("enviar", "kavak", open_tasks), "")


class Classification(unittest.TestCase):
    def test_domains(self):
        cases = [("Cotización para Cemex", "cotizaciones-operativo"),
                 ("Kavak loss prevention weekly", "operacion-kavak"),
                 ("RFP Uber AV field support", "grandes-deals"),
                 ("Automatización de flujo de viajes Ford", "pipeline-estrategico"),
                 ("Diaria Spain Launch Clicars", "reuniones-espana"),
                 ("Revisión de margen semanal", "operacion-semanal")]
        for text, expected in cases:
            self.assertEqual(gate.classify_domain(text), expected, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
