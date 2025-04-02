# Distributed Energy Systems

This repository is dedicated to the development of a distributed macro energy system using DCOP (Distributed Constraint Optimization Problems) and Frodo2.

## Repository Structure

- **Folder Repository**: Contains manually implemented files.
- **Parser Repository**: Contains the parser being developed to automate the environment framing.

## Running Frodo2

To run the `frodo2.18.1.jar` file, follow these steps:

1. Open a terminal window.
2. Navigate to the directory containing the `frodo2.18.1.jar` file.
3. Execute the following command:

    ```sh
    java -Xmx96G -cp "frodo2.18.1.jar:junit-4.13.2.jar:hamcrest-core-1.3.jar" frodo2.algorithms.AgentFactory -timeout 60000000 SAPP_limited_output.xml agents/DPOP/DPOPagentJaCoP.xml -o solution_SAPP_limited.xml
    ```

This will start the Frodo2 application.gf