# DEOpNet
DEOpNet is a research prototype for distributed energy system planning based on Distributed Constraint Optimization Problems (DCOPs) and it stands for "Distributed Energy Optimization Network". Unlike traditional centralized macro-energy models, which assume full cooperation and a single decision-maker, DEOpNet reflects the decentralized nature of international energy planning.

Each country is modeled as an autonomous agent, independently optimizing its energy production and investment decisions, while coordinating cross-border electricity exchanges through structured communication. The model allows for both cooperation and partial information sharing — without relying on a central planner.

The model enables more realistic simulations of international energy coordination and can evaluate the feasibility of decentralized planning outcomes under varied geopolitical, infrastructural, and environmental assumptions.

## Documentation

The full documentation for DEOpNet is available at [https://deopnet.readthedocs.io/](https://deopnet.readthedocs.io/).

## Author

DEOpNet was developed by Valeria Amato and collaborators as part of ongoing research into decentralized energy systems. For inquiries or collaboration opportunities, please contact [Valemto](mailto:valeria.amato@polimi.it).

## Running Frodo2

To run the `frodo2.18.1.jar` file, follow these steps:

1. Open a terminal window.
2. Navigate to the directory containing the `frodo2.18.1.jar` file.
3. Execute the following command:

    ```sh
    java -Xmx8G -cp "frodo2.18.1.jar:junit-4.13.2.jar:hamcrest-core-1.3.jar" frodo2.algorithms.AgentFactory -timeout 60000000 SAPP_limited_output.xml agents/DPOP/DPOPagentJaCoP.xml -o solution_SAPP_limited.xml
    ```

This will start the Frodo2 application.gf