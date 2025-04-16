Run the Frodo Solver
==============




To run the ``frodo2.18.1.jar`` file, follow these steps:

1. Open a terminal window.
2. Navigate to the directory containing the ``frodo2.18.1.jar`` file.
3. Execute the following command:

   .. code-block:: bash

      java -Xmx8G -cp "frodo2.18.1.jar:junit-4.13.2.jar:hamcrest-core-1.3.jar" \
      frodo2.algorithms.AgentFactory -timeout 60000000 problem.xml \
      agents/DPOP/DPOPagentJaCoP.xml -o solution.xml
