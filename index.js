const core = require("@actions/core");
const exec = require("@actions/exec");
const setupPython = require("./src/setup-python");

async function run() {
  try {
    // Allows ncc to find assets to be included in the distribution
    const src = __dirname + "/src";
    core.debug(`src: ${src}`);

    // Setup Python from the tool cache
    setupPython("3.8.x", "x64");

    // Install requirements
    await exec.exec("pip", [
      "install",
      "-r",
      `${src}/requirements.txt`,
      "--no-index",
      `--find-links=${__dirname}/vendor`
    ]);

    // Fetch action inputs
    const inputs = {
      token: core.getInput("token") || process.env.GITHUB_TOKEN,
      repository: core.getInput("repository") || process.env.GITHUB_REPOSITORY,
      version: core.getInput("version") || process.env.VERSION,
      path: core.getInput("path") || "./CHANGELOG.md",
      action: core.getInput("action") || "release"
    };
    core.debug(`Inputs: ${JSON.stringify(inputs)}`);

    // Set environment variables from inputs.
    if (inputs.token) process.env.GITHUB_TOKEN = inputs.token;
    if (inputs.repository) process.env.GITHUB_REPOSITORY = inputs.repository;

    // Execute python script
    const options = {};
    let pythonOutput = "";
    options.listeners = {
      stdout: data => {
        pythonOutput += data.toString();
      }
    };
    await exec.exec(
      "python",
      [`${src}/main.py`, "-v", inputs.version],
      options
    );

    // Process output
    core.debug("OUTPUT");
    core.debug(pythonOutput);
    let outputJSON = JSON.parse(pythonOutput);
    Object.keys(outputJSON).forEach(key => {
      let value = outputJSON[key];
      core.setOutput(key, value);
    });
  } catch (error) {
    core.setFailed(error.message);
  }
}

run();
