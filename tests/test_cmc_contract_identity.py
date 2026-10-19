from scripts.research.report_cmc_contract_identity import match


def test_evm_case_and_chain():
    source = {"platformName": "Ethereum", "tokenAddress": "0xabCD"}
    currency = {"supported_networks": [{"id": "ethereum", "contract_address": "0xABcd"}]}
    assert match(source, currency) == "MATCHING_CHAIN_AND_CONTRACT_PROPOSAL"
    currency["supported_networks"][0]["id"] = "base"
    assert match(source, currency).startswith("UNRESOLVED")


def test_solana_case_sensitive_and_native_unknown():
    source = {"platformName": "Solana", "tokenAddress": "AbC"}
    assert match(source, {"supported_networks": [{"id": "solana", "contract_address": "abc"}]}).startswith("UNRESOLVED")
    assert match({}, {}) == "UNRESOLVED_NO_CONTRACT"
