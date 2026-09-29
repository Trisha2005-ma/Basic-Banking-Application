import pytest

from app.repositories.transaction_repository import TransactionRepository



def balance(client, headers):
    return client.get("/api/accounts/me", headers=headers).json()["balance"]


def test_get_my_account(client, auth):
    res = client.get("/api/accounts/me", headers=auth)
    assert res.status_code == 200
    body = res.json()
    assert body["accountHolderName"] == "John Doe"
    assert body["balance"] == 0
    assert {"accountId", "accountNumber", "createdAt"} <= body.keys()


def test_requested_banking_routes_are_available(client, auth, second_user):
    receiver_headers, _ = second_user
    receiver_id = client.get("/api/account", headers=receiver_headers).json()["accountId"]

    account = client.get("/api/account", headers=auth)
    deposit = client.post("/api/deposit", json={"amount": 100}, headers=auth)
    withdraw = client.post("/api/withdraw", json={"amount": 25}, headers=auth)
    transfer = client.post(
        "/api/transfer",
        json={"receiverAccountId": receiver_id, "amount": 25},
        headers=auth,
    )

    assert account.status_code == 200
    assert deposit.status_code == 200
    assert withdraw.status_code == 200
    assert transfer.status_code == 200
    assert client.get("/api/account", headers=auth).json()["balance"] == 50


def test_deposit_success(client, auth):
    res = client.post("/api/accounts/deposit", json={"amount": 5000}, headers=auth)
    assert res.status_code == 200
    assert res.json()["balance"] == 5000
    assert res.json()["transaction"]["type"] == "DEPOSIT"
    assert balance(client, auth) == 5000


@pytest.mark.parametrize("amount", [0, -10, "abc", 10.999])
def test_deposit_invalid_amount(client, auth, amount):
    res = client.post("/api/accounts/deposit", json={"amount": amount}, headers=auth)
    assert res.status_code == 422
    assert balance(client, auth) == 0


def test_deposit_requires_auth(client):
    assert client.post("/api/accounts/deposit", json={"amount": 10}).status_code == 401


def test_withdraw_success(client, auth):
    client.post("/api/accounts/deposit", json={"amount": 5000}, headers=auth)
    res = client.post("/api/accounts/withdraw", json={"amount": 2000}, headers=auth)
    assert res.status_code == 200
    assert res.json()["balance"] == 3000


@pytest.mark.parametrize("amount", [0, -5])
def test_withdraw_invalid_amount(client, auth, amount):
    res = client.post("/api/accounts/withdraw", json={"amount": amount}, headers=auth)
    assert res.status_code == 422


def test_withdraw_insufficient_balance(client, auth):
    client.post("/api/accounts/deposit", json={"amount": 100}, headers=auth)
    res = client.post("/api/accounts/withdraw", json={"amount": 100.01}, headers=auth)
    assert res.status_code == 400
    assert res.json()["detail"] == "Insufficient balance"
    assert balance(client, auth) == 100


def test_transfer_success(client, auth, second_user):
    jane_headers, jane_info = second_user
    jane_id = client.get("/api/accounts/me", headers=jane_headers).json()["accountId"]
    client.post("/api/accounts/deposit", json={"amount": 5000}, headers=auth)

    res = client.post(
        "/api/accounts/transfer",
        json={"receiverAccountId": jane_id, "amount": 1500},
        headers=auth,
    )
    assert res.status_code == 200
    assert balance(client, auth) == 3500
    assert balance(client, jane_headers) == 1500

    jane_txs = client.get("/api/accounts/transactions", headers=jane_headers).json()
    assert [t["type"] for t in jane_txs] == ["TRANSFER_CREDIT"]


def test_transfer_to_self(client, auth):
    my_id = client.get("/api/accounts/me", headers=auth).json()["accountId"]
    client.post("/api/accounts/deposit", json={"amount": 100}, headers=auth)
    res = client.post(
        "/api/accounts/transfer",
        json={"receiverAccountId": my_id, "amount": 10},
        headers=auth,
    )
    assert res.status_code == 400


def test_transfer_unknown_receiver(client, auth):
    client.post("/api/accounts/deposit", json={"amount": 100}, headers=auth)
    res = client.post(
        "/api/accounts/transfer",
        json={"receiverAccountId": 9999, "amount": 10},
        headers=auth,
    )
    assert res.status_code == 404
    assert balance(client, auth) == 100


@pytest.mark.parametrize("receiver", [0, -1, "abc"])
def test_transfer_invalid_receiver_id(client, auth, receiver):
    res = client.post(
        "/api/accounts/transfer",
        json={"receiverAccountId": receiver, "amount": 10},
        headers=auth,
    )
    assert res.status_code == 422


def test_transfer_insufficient_balance(client, auth, second_user):
    jane_headers, _ = second_user
    jane_id = client.get("/api/accounts/me", headers=jane_headers).json()["accountId"]
    res = client.post(
        "/api/accounts/transfer",
        json={"receiverAccountId": jane_id, "amount": 10},
        headers=auth,
    )
    assert res.status_code == 400
    assert balance(client, jane_headers) == 0


def test_transfer_is_atomic_when_database_fails(client, auth, second_user, monkeypatch):
    jane_headers, _ = second_user
    jane_id = client.get("/api/accounts/me", headers=jane_headers).json()["accountId"]
    client.post("/api/accounts/deposit", json={"amount": 5000}, headers=auth)

    original = TransactionRepository.create
    calls = {"n": 0}

    def flaky_create(self, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:  # fail on the second row of the transfer
            raise RuntimeError("simulated database failure")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(TransactionRepository, "create", flaky_create)

    with pytest.raises(RuntimeError):
        client.post(
            "/api/accounts/transfer",
            json={"receiverAccountId": jane_id, "amount": 1500},
            headers=auth,
        )

    monkeypatch.undo()
    assert balance(client, auth) == 5000
    assert balance(client, jane_headers) == 0
    history = client.get("/api/accounts/transactions", headers=auth).json()
    assert [t["type"] for t in history] == ["DEPOSIT"]


def test_transactions_only_show_own(client, auth, second_user):
    jane_headers, _ = second_user
    client.post("/api/accounts/deposit", json={"amount": 5000}, headers=auth)
    client.post("/api/accounts/withdraw", json={"amount": 1000}, headers=auth)
    client.post("/api/accounts/deposit", json={"amount": 7}, headers=jane_headers)

    mine = client.get("/api/accounts/transactions", headers=auth).json()
    hers = client.get("/api/accounts/transactions", headers=jane_headers).json()
    assert [(t["type"], t["amount"]) for t in mine] == [("DEPOSIT", 5000), ("WITHDRAW", 1000)]
    assert [(t["type"], t["amount"]) for t in hers] == [("DEPOSIT", 7)]
    assert {"id", "type", "amount", "status", "createdAt"} <= mine[0].keys()


def test_transactions_requires_auth(client):
    assert client.get("/api/accounts/transactions").status_code == 401
