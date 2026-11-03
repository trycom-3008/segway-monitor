"""Explicit, experimental owner pairing for already paired Encryption2 devices.

The WLBT backend was observed requesting SET_PWD even with the stored-password
flag set. This proves the requested next step, not scooter acceptance of it.
No WLBT code or server is used here. Protocol machinery is scootscoot 0.1.2,
Apache-2.0 (andyshinn; protocol/crypto lineage NootNooot, see bundled NOTICE).

Normal read sessions retain the upstream policy. Only a deliberately created
OwnerPairingScooter can negotiate a new key. Every new key must be encrypted
and persisted by the caller before a SET_PWD frame can leave this module.
"""

import secrets

from scootscoot import BoardRole, HandshakeFailed, PairingRequired, PairingTimeout, Scooter, __version__
from scootscoot.framing import CMD_SET_PWD, build_frame
from scootscoot.handshake import (
    CONFIRM_TIMEOUT, Established, Handshake, Send, SET_PWD_ATTEMPTS,
)


class Gt3DHandshake(Handshake):
    """Handshake stays in initial mode until AUTH succeeds, then SN traffic.

    The WLBT SET_PWD packet was observed with counter 0 on this GT3 D. The
    complete sequence remains experimental until accepted by real hardware.
    """

    def _begin_auth(self):
        self._crypto.reset_sn()
        return super()._begin_auth()

    def _feed_auth(self, raw):
        established = super()._feed_auth(raw)
        established.crypto.start_sn()
        return established


class OwnerHandshake(Gt3DHandshake):
    def __init__(self, *, persist_password, **kwargs):
        if __version__ != "0.1.2":
            raise RuntimeError("Diese Kopplungsoption ist nur mit scootscoot 0.1.2 geprüft.")
        if kwargs.get("password") is not None:
            raise ValueError("Neue Kopplungen verwenden einen frisch erzeugten Schlüssel.")
        if not callable(persist_password):
            raise ValueError("Eine Schlüsselsicherung ist erforderlich.")
        super().__init__(allow_pairing=True, **kwargs)
        self._persist_password = persist_password

    def _feed_pre_comm(self, raw):
        try:
            return super()._feed_pre_comm(raw)
        except PairingRequired:
            # Upstream has already verified PRE_COMM and populated _auth,
            # _serial and SN mode. Its stored-password check is local policy.
            # Explicit owner pairing deliberately tries the documented SET_PWD.
            return self._begin_set_pwd()

    def _begin_set_pwd(self):
        self._password = secrets.token_bytes(16)
        # Saving must succeed BEFORE encryption/return of the outbound frame.
        self._persist_password(self._password)
        self._crypto.set_key(self._name, self._auth)
        self._crypto.reset_sn()
        self._paired = True
        self._phase = type(self._phase).SET_PWD
        payload = self._crypto.encrypt(build_frame(
            self._ble, CMD_SET_PWD, 0x00, self._password, sync2=self._sync2))
        # Some firmware stays silent until the physical button is pressed,
        # rather than first returning a "pending" acknowledgement. Allow
        # human confirmation time on the first SET_PWD exchange itself.
        return Send(payload, CONFIRM_TIMEOUT, SET_PWD_ATTEMPTS)


class Gt3DReadScooter(Scooter):
    async def _make_handshake(self, client, *, allow_pairing):
        if allow_pairing:
            raise PairingRequired("Die neue Kopplung muss über die gesonderte Besitzeraktion gestartet werden.")
        return Gt3DHandshake(
            device_name=await self._key_material(client), suite=self._profile.crypto,
            ble_address=self._profile.board(BoardRole.BLE).address,
            password=self._credentials.password, allow_pairing=False)

    def _emit_status(self, message):
        pass

    async def _handshake(self, client, transport, *, allow_pairing):
        handshake = await self._make_handshake(client, allow_pairing=allow_pairing)
        step = handshake.start()
        while True:
            if isinstance(step, Established):
                return step
            if isinstance(step, Send):
                if handshake._phase.name == "SET_PWD":
                    self._emit_status("Neue Kopplung angefordert · bitte jetzt Power-Taste am Scooter drücken (bis zu 60 s)")
                try:
                    response = await self._exchange(transport, step)
                except HandshakeFailed as error:
                    if handshake._phase.name == "SET_PWD":
                        raise PairingTimeout("Keine Bestätigung auf die neue Kopplungsanfrage.") from error
                    raise
                step = handshake.feed(response)
                continue
            self._emit_status("Bestätigung am Scooter erforderlich · Power-Taste drücken (bis zu 60 s)")
            try:
                raw = await transport.recv(step.timeout)
            except TimeoutError as error:
                raise PairingTimeout("Die Kopplung wurde am Fahrzeug nicht bestätigt.") from error
            step = handshake.feed(raw)


class OwnerPairingScooter(Gt3DReadScooter):
    def __init__(self, *args, persist_password, emit_status, **kwargs):
        super().__init__(*args, **kwargs)
        self._persist_owner_password = persist_password
        self._emit_owner_status = emit_status

    def _emit_status(self, message):
        self._emit_owner_status(message)

    async def _make_handshake(self, client, *, allow_pairing):
        if not allow_pairing:
            return await super()._make_handshake(client, allow_pairing=False)
        return OwnerHandshake(
            device_name=await self._key_material(client), suite=self._profile.crypto,
            ble_address=self._profile.board(BoardRole.BLE).address,
            persist_password=self._persist_owner_password)
