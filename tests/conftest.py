import pytest

from rasa import server
from rasa.core import config
from rasa.core.agent import Agent, load_agent
from rasa.core.channels import RestInput, channel
from rasa.core.policies import AugmentedMemoizationPolicy
from rasa.train import train_async
from tests.core.conftest import (
    DEFAULT_STORIES_FILE,
    DEFAULT_DOMAIN_PATH,
    DEFAULT_STACK_CONFIG,
    DEFAULT_NLU_DATA,
    END_TO_END_STORY_FILE,
)
from tests.nlu.conftest import CONFIG_DEFAULTS_PATH

DEFAULT_CONFIG_PATH = "rasa/cli/default_config.yml"


@pytest.fixture
async def default_agent(tmpdir_factory) -> Agent:
    model_path = tmpdir_factory.mktemp("model").strpath

    agent = Agent(
        "data/test_domains/default.yml",
        policies=[AugmentedMemoizationPolicy(max_history=3)],
    )

    training_data = await agent.load_data(DEFAULT_STORIES_FILE)
    agent.train(training_data)
    agent.persist(model_path)
    return agent


@pytest.fixture
async def stack_agent(trained_rasa_model) -> Agent:
    return await load_agent(trained_rasa_model, None, None, None)


@pytest.fixture
async def core_agent(trained_core_model) -> Agent:
    return await load_agent(trained_core_model, None, None, None)


@pytest.fixture
async def nlu_agent(trained_nlu_model) -> Agent:
    return await load_agent(trained_nlu_model, None, None, None)


@pytest.fixture(scope="session")
def default_domain_path():
    return DEFAULT_DOMAIN_PATH


@pytest.fixture(scope="session")
def default_stories_file():
    return DEFAULT_STORIES_FILE


@pytest.fixture(scope="session")
def default_stack_config():
    return DEFAULT_STACK_CONFIG


@pytest.fixture(scope="session")
def default_nlu_data():
    return DEFAULT_NLU_DATA


@pytest.fixture(scope="session")
def end_to_end_story_file():
    return END_TO_END_STORY_FILE


@pytest.fixture(scope="session")
def default_config():
    return config.load(DEFAULT_CONFIG_PATH)


@pytest.fixture()
async def trained_rasa_model(
    default_domain_path, default_config, default_nlu_data, default_stories_file
):
    clean_folder("models")
    trained_stack_model_path = await train_async(
        domain="data/test_domains/default.yml",
        config=DEFAULT_STACK_CONFIG,
        training_files=[default_nlu_data, default_stories_file],
    )

    return trained_stack_model_path


@pytest.fixture()
async def trained_core_model(
    default_domain_path, default_config, default_nlu_data, default_stories_file
):
    trained_core_model_path = await train_async(
        domain=default_domain_path,
        config=DEFAULT_STACK_CONFIG,
        training_files=[default_stories_file],
    )

    return trained_core_model_path


@pytest.fixture()
async def trained_nlu_model(
    default_domain_path, default_config, default_nlu_data, default_stories_file
):
    trained_nlu_model_path = await train_async(
        domain=default_domain_path,
        config=DEFAULT_STACK_CONFIG,
        training_files=[default_nlu_data],
    )

    return trained_nlu_model_path


@pytest.fixture
async def rasa_server(stack_agent):
    app = server.create_app(agent=stack_agent)
    channel.register([RestInput()], app, "/webhooks/")
    return app


@pytest.fixture
async def rasa_core_server(core_agent):
    app = server.create_app(agent=core_agent)
    channel.register([RestInput()], app, "/webhooks/")
    return app


@pytest.fixture
async def rasa_nlu_server(nlu_agent):
    app = server.create_app(agent=nlu_agent)
    channel.register([RestInput()], app, "/webhooks/")
    return app


@pytest.fixture
async def rasa_server_secured(default_agent):
    app = server.create_app(agent=default_agent, auth_token="rasa", jwt_secret="core")
    channel.register([RestInput()], app, "/webhooks/")
    return app


def clean_folder(folder):
    import os

    if os.path.exists(folder):
        import shutil

        shutil.rmtree(folder)
