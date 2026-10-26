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


class ClientAsksArmando(unittest.TestCase):
    """Gate 4: a client or prospect asking Armando something is a task even
    without a promise. Borusan was suppressed three times for lack of this."""

    def test_prospect_asking_armando_is_accepted(self):
        for text, sender in [
            ("Hi Armando, thanks for the call. Could you share the pricing for the Monterrey lanes?",
             "mehmet.yilmaz@borusan.com"),
            ("Armando, adjunto los resultados del piloto. Quedamos atentos a su propuesta comercial.",
             "direccion@grupoautosur.com"),
            ("Buen día. ¿Cuándo nos confirman los conductores de Mérida?",
             "logistica@cliente-nuevo.mx"),
        ]:
            v = gate.evaluate(item(text, subject="Re: Borusan / Draiver", sender=sender))
            self.assertTrue(v["accept"], text)
            self.assertEqual(v["reason"], "cliente_espera_respuesta", text)

    def test_counterparty_is_the_prospect(self):
        v = gate.evaluate(item("Could you send us the proposal by email?",
                               sender="mehmet.yilmaz@borusan.com"))
        self.assertEqual(v["counterparty"], "borusan")
        self.assertEqual(v["action"], "enviar")

    def test_question_to_the_team_is_not_armandos(self):
        # Tesla dispatch threads go to the whole ops list; the ask is theirs.
        team = ["armando.flores@driverdo.com", "uriel.vargas@driverdo.com",
                "julia.diaz@draiver.com", "jose.duran@driverdo.com"]
        v = gate.evaluate(item("Can you confirm the drivers for tomorrow's dispatch?",
                               sender="dispatch@tesla.com", recipients=team))
        self.assertFalse(v["accept"])
        v = gate.evaluate(item("Armando, can you confirm the drivers for tomorrow?",
                               sender="dispatch@tesla.com", recipients=team))
        self.assertTrue(v["accept"])

    def test_noise_stays_out(self):
        cases = [
            ("Your weekly recommendations are ready. Could you rate them?", "noreply@linkedin.com", ""),
            ("Tu recibo está disponible. ¿Tienes dudas sobre tu viaje?", "uber.mexico@uber.com", "Tu recibo #R59"),
            ("¿Cómo estás? Saludos a todos por allá.", "amigo@gmail.com", ""),
            ("Hola Armando, ¿cómo estás?", "ana@cliente.com", ""),
            ("Gracias, quedo atento.", "ana@cliente.com", ""),
            ("Maybe we could look at Q1 together, what do you think?", "ana@cliente.com", ""),
        ]
        for text, sender, subject in cases:
            v = gate.evaluate(item(text, subject=subject, sender=sender))
            self.assertFalse(v["accept"], text)

    def test_internal_sender_never_uses_this_gate(self):
        v = gate.evaluate(item("¿Me ayudas a revisar la tarifa de Cemex?",
                               sender="julia.diaz@draiver.com"))
        self.assertFalse(v["accept"])


class DedupeAtCreation(unittest.TestCase):
    def test_same_action_same_counterparty_suppressed(self):
        open_tasks = [{"status": "open", "archived": False, "code": "T-7",
                       "action": "enviar", "counterparty": "kavak"}]
        self.assertEqual(gate.is_duplicate("enviar", "kavak", open_tasks), "T-7")

    def test_same_action_other_counterparty_passes(self):
        open_tasks = [{"status": "open", "archived": False, "code": "T-7",
                       "action": "enviar", "counterparty": "kavak"}]
        self.assertEqual(gate.is_duplicate("enviar", "clicars", open_tasks), "")

    def test_same_thread_other_action_suppressed(self):
        # T-34 (confirmar) y T-77 (enviar): un solo hilo REPSE con Garrigues.
        open_tasks = [{"status": "open", "archived": False, "code": "T-34",
                       "action": "confirmar", "counterparty": "garrigues",
                       "title": "Seguimiento con Garrigues: REPSE and digital platforms"}]
        self.assertEqual(gate.is_duplicate("enviar", "garrigues", open_tasks,
                                           subject="Re: REPSE and digital platforms"), "T-34")
        self.assertEqual(gate.is_duplicate("enviar", "kavak", open_tasks,
                                           subject="Re: REPSE and digital platforms"), "")

    def test_closed_task_does_not_block(self):
        open_tasks = [{"status": "done", "archived": False, "code": "T-7",
                       "action": "enviar", "counterparty": "kavak"}]
        self.assertEqual(gate.is_duplicate("enviar", "kavak", open_tasks), "")


class TitlesSayWhatToDo(unittest.TestCase):
    def test_client_ask_leads_with_the_verb(self):
        it = item("Could you send us the proposal?", subject="RE: Borusan / Draiver",
                  sender="mehmet.yilmaz@borusan.com")
        self.assertEqual(gate.task_title(gate.evaluate(it), it), "Enviar a Borusan: Borusan / Draiver")

    def test_someone_elses_promise_is_a_follow_up(self):
        it = item("Les envío la prefactura para que nos apoyen con el pago.",
                  subject="Re: RANGER | GRIS CARBONO", sender="pagos@zapata.com")
        self.assertEqual(gate.task_title(gate.evaluate(it), it), "Seguimiento con Zapata: RANGER | GRIS CARBONO")

    def test_armandos_own_promise(self):
        it = item("Te mando la cotización de Kavak antes del 5.", subject="RV: Cotización CDMX",
                  sender="armando.flores@driverdo.com", recipients=["ana@kavak.com"])
        self.assertEqual(gate.task_title(gate.evaluate(it), it), "Enviar a Kavak: Cotización CDMX")


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
