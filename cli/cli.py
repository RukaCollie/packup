import io
from pydantic_core import Url
import requests
import click
from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class PackFile(BaseModel):
    class Config:
        alias_generator = to_camel

    path: str
    hashes: dict[str, str]
    env: dict[str, str]
    downloads: list[str]
    file_size: int


class ModrinthPack(BaseModel):
    class Config:
        alias_generator = to_camel

    format_version: int
    game: str
    name: str
    version_id: str
    summary: str | None
    files: list[PackFile]
    dependencies: dict[str, str]


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--input",
    required=True,
    type=click.File("r"),
    default="modrinth.index.json",
    help="Modrinth index json file to read",
)
def info(input: io.TextIOWrapper) -> None:
    """Read input file and print info"""

    # takes an input file and reads all the data inside of it
    # in this case, file_data is a text string full of json data
    file_data = input.read()

    # pass the json data to our model and validate it as a real python object
    # this object will be an instance of the class ModrinthPack
    # throws ValidationError if the json data isn't in the shape of a ModrinthPack
    mrpack = ModrinthPack.model_validate_json(file_data)

    # do something with the mrpack object
    click.secho(f"Found {len(mrpack.files)} files in modpack", fg="green")

    # for every file in mrpack
    # for file in mrpack.files:
    #     click.secho(f"{file.path} ({file.file_size} bytes)")

    # on the first file in the modpack
    file = mrpack.files[0]
    click.secho(f"{file.path} ({file.file_size} bytes)")

    # REST API
    # REST REpresentational State Transfer "RESTful"
    # API application programmer interface
    # HTTP is the protocol
    #   it has verbs!
    #   GET me a thing
    #   PUT a thing here
    #   POST a thing somewhere
    #   DELETE a thing
    # nearly always use JSON in the HTTP body

    # things that store state (modrinth DB
    # things that modify state (this application we're making)
    # things that provide access to state or communicate state (a REST API)

    # ASSUMPTIONS
    # 1. every file is a modrinth hosted project (i.e. a mod)
    # 2. every file has a download URL
    # 3. every download URL is a modrinth URL
    # 4. the first download URL is the modrinth URL

    # call Modrinth API for a project (sodium)
    click.secho(f"file download path: {file.downloads[0]}")
    # download path has the structure:
    # https://<modrinth cdn>/data/<project ID>/versions/<project version ID>/<filename>
    download = Url(file.downloads[0])

    # check the URL path is not None
    if not download.path:
        raise Exception("Download path doesn't exist or it's invalid")

    # split up the URL path
    url_parts = download.path.split("/")
    click.secho(f"split {download.path} into url_parts")
    click.secho(url_parts, fg="yellow")

    # get the bits of the path that we're interested in
    project_id = url_parts[2]
    project_version_id = url_parts[4]
    filename = url_parts[5]

    # print the information we found
    click.secho(f"modrinth file project_id: {project_id}")
    click.secho(f"modrinth file project_version_id: {project_version_id}")
    click.secho(f"modrinth file filename: {filename}")

    # call the modrinth API with the project_id we now know
    request_data = requests.get(f"https://api.modrinth.com/v2/project/{project_id}")

    # this prints the whole API response - it's noisy so we commented it
    # click.echo(json.dumps(request_data.json(), indent=2))

    # take the API response and get the client or server info we want to know
    request_json = request_data.json()
    client_side = request_json["client_side"]
    server_side = request_json["server_side"]
    click.secho(f"client support: {client_side}")
    click.secho(f"server support: {server_side}")
