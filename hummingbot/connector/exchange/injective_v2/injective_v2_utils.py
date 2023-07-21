from abc import ABC, abstractmethod
from decimal import Decimal
from typing import TYPE_CHECKING, Dict, Union

from pydantic import Field, SecretStr
from pydantic.class_validators import validator
from pyinjective.constant import Network

from hummingbot.client.config.config_data_types import BaseClientModel, BaseConnectorConfigMap, ClientFieldData
from hummingbot.connector.exchange.injective_v2.injective_data_source import (
    InjectiveGranteeDataSource,
    InjectiveVaultsDataSource,
)
from hummingbot.core.data_type.trade_fee import TradeFeeSchema

if TYPE_CHECKING:
    from hummingbot.connector.exchange.injective_v2.injective_data_source import InjectiveDataSource

CENTRALIZED = False
EXAMPLE_PAIR = "INJ-USDT"

DEFAULT_FEES = TradeFeeSchema(
    maker_percent_fee_decimal=Decimal("0"),
    taker_percent_fee_decimal=Decimal("0"),
)

MAINNET_NODES = ["lb", "sentry0", "sentry1", "sentry3"]


class InjectiveNetworkMode(BaseClientModel, ABC):
    @abstractmethod
    def network(self) -> Network:
        pass

    @abstractmethod
    def use_secure_connection(self) -> bool:
        pass


class InjectiveMainnetNetworkMode(InjectiveNetworkMode):

    node: str = Field(
        default="lb",
        client_data=ClientFieldData(
            prompt=lambda cm: ("Enter the mainnet node you want to connect to"),
            prompt_on_new=True
        ),
    )

    class Config:
        title = "mainnet_network"

    @validator("node", pre=True)
    def validate_node(cls, v: str):
        if v not in MAINNET_NODES:
            raise ValueError(f"{v} is not a valid node ({MAINNET_NODES})")
        return v

    def network(self) -> Network:
        return Network.mainnet(node=self.node)

    def use_secure_connection(self) -> bool:
        return self.node == "lb"


class InjectiveTestnetNetworkMode(InjectiveNetworkMode):
    def network(self) -> Network:
        return Network.testnet()

    def use_secure_connection(self) -> bool:
        return True

    class Config:
        title = "testnet_network"


class InjectiveCustomNetworkMode(InjectiveNetworkMode):
    lcd_endpoint: str = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: ("Enter the network lcd_endpoint"),
            prompt_on_new=True
        ),
    )
    tm_websocket_endpoint: str = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: ("Enter the network tm_websocket_endpoint"),
            prompt_on_new=True
        ),
    )
    grpc_endpoint: str = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: ("Enter the network grpc_endpoint"),
            prompt_on_new=True
        ),
    )
    grpc_exchange_endpoint: str = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: ("Enter the network grpc_exchange_endpoint"),
            prompt_on_new=True
        ),
    )
    grpc_explorer_endpoint: str = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: ("Enter the network grpc_explorer_endpoint"),
            prompt_on_new=True
        ),
    )
    chain_id: str = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: ("Enter the network chain_id"),
            prompt_on_new=True
        ),
    )
    env: str = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: ("Enter the network environment name"),
            prompt_on_new=True
        ),
    )
    secure_connection: bool = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: ("Should this configuration use secure connections? (yes/no)"),
            prompt_on_new=True
        ),
    )

    class Config:
        title = "custom_network"

    def network(self) -> Network:
        return Network.custom(
            lcd_endpoint=self.lcd_endpoint,
            tm_websocket_endpoint=self.tm_websocket_endpoint,
            grpc_endpoint=self.grpc_endpoint,
            grpc_exchange_endpoint=self.grpc_exchange_endpoint,
            grpc_explorer_endpoint=self.grpc_explorer_endpoint,
            chain_id=self.chain_id,
            env=self.env,
        )

    def use_secure_connection(self) -> bool:
        return self.secure_connection


NETWORK_MODES = {
    InjectiveMainnetNetworkMode.Config.title: InjectiveNetworkMode,
    InjectiveTestnetNetworkMode.Config.title: InjectiveTestnetNetworkMode,
    InjectiveCustomNetworkMode.Config.title: InjectiveCustomNetworkMode,
}


class InjectiveAccountMode(BaseClientModel, ABC):

    @abstractmethod
    def create_data_source(self, network: Network, use_secure_connection: bool) -> "InjectiveDataSource":
        pass


class InjectiveDelegatedAccountMode(InjectiveAccountMode):
    private_key: SecretStr = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter your Injective trading account private key",
            is_secure=True,
            is_connect_key=True,
            prompt_on_new=True,
        ),
    )
    subaccount_index: int = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter your Injective trading account subaccount index",
            prompt_on_new=True,
        ),
    )
    granter_address: str = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter the Injective address of the granter account (portfolio account)",
            prompt_on_new=True,
        ),
    )
    granter_subaccount_index: int = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter the Injective granter subaccount index (portfolio subaccount index)",
            prompt_on_new=True,
        ),
    )

    class Config:
        title = "delegate_account"

    def create_data_source(self, network: Network, use_secure_connection: bool) -> "InjectiveDataSource":
        return InjectiveGranteeDataSource(
            private_key=self.private_key.get_secret_value(),
            subaccount_index=self.subaccount_index,
            granter_address=self.granter_address,
            granter_subaccount_index=self.granter_subaccount_index,
            network=network,
            use_secure_connection=use_secure_connection,
        )


class InjectiveVaultAccountMode(InjectiveAccountMode):
    private_key: SecretStr = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter the vault admin private key",
            is_secure=True,
            is_connect_key=True,
            prompt_on_new=True,
        ),
    )
    subaccount_index: int = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter the vault admin subaccount index",
            prompt_on_new=True,
        ),
    )
    vault_contract_address: str = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter the vault contract address",
            prompt_on_new=True,
        ),
    )
    vault_subaccount_index: int = Field(
        default=1,
        const=True,
        client_data=None
    )

    class Config:
        title = "vault_account"

    def create_data_source(self, network: Network, use_secure_connection: bool) -> "InjectiveDataSource":
        return InjectiveVaultsDataSource(
            private_key=self.private_key.get_secret_value(),
            subaccount_index=self.subaccount_index,
            vault_contract_address=self.vault_contract_address,
            vault_subaccount_index=self.vault_subaccount_index,
            network=network,
            use_secure_connection=use_secure_connection,
        )


ACCOUNT_MODES = {
    InjectiveDelegatedAccountMode.Config.title: InjectiveDelegatedAccountMode,
    InjectiveVaultAccountMode.Config.title: InjectiveVaultAccountMode,
}


class InjectiveConfigMap(BaseConnectorConfigMap):
    connector: str = Field(default="injective_v2", const=True, client_data=None)
    receive_connector_configuration: bool = Field(default=True, const=True, client_data=None)
    network: Union[tuple(NETWORK_MODES.values())] = Field(
        default=InjectiveMainnetNetworkMode(),
        client_data=ClientFieldData(
            prompt=lambda cm: f"Select the network ({'/'.join(list(NETWORK_MODES.keys()))})",
            prompt_on_new=True,
        ),
    )
    account_type: Union[tuple(ACCOUNT_MODES.values())] = Field(
        default=InjectiveDelegatedAccountMode(
            private_key="0000000000000000000000000000000000000000000000000000000000000000",  # noqa: mock
            subaccount_index=0,
            granter_address="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  # noqa: mock
            granter_subaccount_index=0,
        ),
        client_data=ClientFieldData(
            prompt=lambda cm: f"Select the type of account configuration ({'/'.join(list(ACCOUNT_MODES.keys()))})",
            prompt_on_new=True,
        ),
    )

    class Config:
        title = "injective_v2"

    @validator("network", pre=True)
    def validate_network(cls, v: Union[(str, Dict) + tuple(NETWORK_MODES.values())]):
        if isinstance(v, tuple(NETWORK_MODES.values()) + (Dict,)):
            sub_model = v
        elif v not in NETWORK_MODES:
            raise ValueError(
                f"Invalid network, please choose a value from {list(NETWORK_MODES.keys())}."
            )
        else:
            sub_model = NETWORK_MODES[v].construct()
        return sub_model

    @validator("account_type", pre=True)
    def validate_account_type(cls, v: Union[(str, Dict) + tuple(ACCOUNT_MODES.values())]):
        if isinstance(v, tuple(ACCOUNT_MODES.values()) + (Dict,)):
            sub_model = v
        elif v not in ACCOUNT_MODES:
            raise ValueError(
                f"Invalid account type, please choose a value from {list(ACCOUNT_MODES.keys())}."
            )
        else:
            sub_model = ACCOUNT_MODES[v].construct()
        return sub_model

    def create_data_source(self):
        return self.account_type.create_data_source(
            network=self.network.network(), use_secure_connection=self.network.use_secure_connection()
        )


KEYS = InjectiveConfigMap.construct()