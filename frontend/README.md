# ThroughPut Testing Application

## Overview

The ThroughPut Testing Application is a React-based tool designed to automate and streamline the testing process for the ThroughPut system. It allows users to upload test cases, run them against the backend via WebSocket connections, and view detailed results of the tests, including product and feature accuracy metrics.

## Features

- Upload test cases in CSV format
- Run tests automatically using WebSocket connections
- Real-time progress tracking of test execution
- Detailed results display, including pass/fail status, product accuracy, and feature accuracy metrics
- Ability to pause, resume, and retry failed tests
- JSON viewer for easy comparison of expected and actual outputs

## Prerequisites

- Node.js (v14.0.0 or later)
- npm (v6.0.0 or later)

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/your-repo/throughput-testing-app.git
   cd throughput-testing-app
   ```

2. Install dependencies:
   ```
   npm install
   ```

## Running the Application

1. Start the development server:

   ```
   npm run dev
   ```

2. Open your browser and navigate to `http://localhost:5173` (or the port specified by Vite).

## Usage

1. Prepare a CSV file with test cases in the following format:

   ```csv
   prompt,name,size,form,processor,processorTDP,memory,io,manufacturer,operatingSystem,environmentals,certifications,summary
   What are the top Computer on Modules available with high memory and I/O count?,Computer On Modules,95 x 95 mm,COM Express Compact Module Type 6,6th Gen Intel Core / Celeron Processors,15W,"Dual Channel DDR4 SODIMM sockets, up to 32GB","SATA Ports: 2 (Gen3 6Gb/s, Gen2 3Gb/s), USB Ports: 8 (4 USB 3.0, 4 USB 2.0), PCI Express: 1 x16 PEG, 7 x1 PCIe, HD Audio, LPC, SMBus, I2C Bus, Ethernet: Intel i219LM (10/100/1000 Mbps)",Advantech,Linux,"Operating Temperature: 0°C to 60°C, Humidity: 0% to 90% (non-condensing)","CE, FCC Class A","A high-performance, low-power Computer On Module with 6th Gen Intel Core and Celeron Processors, supporting dual channel DDR4 memory, multiple display outputs, and extensive I/O interfaces."
   ```

2. Upload the CSV file using the file input on the application's interface.

3. Click the "Create Test" button to create a new test with the uploaded cases.

4. Select the created test from the test list and click the "Run Test" button to start the test execution.

5. Monitor the progress bar and real-time statistics as tests are executed.

6. Once complete, view the detailed results, including:
   - Overall pass/fail count
   - Product accuracy percentage
   - Feature accuracy percentage
   - Individual test case results with expected and actual outputs

## Project Structure

- `src/`
  - `components/`
    - `cards/`
      - `CreateTestCard.tsx`: Handles test creation from uploaded CSV
      - `TestExecutionCard.tsx`: Manages the execution of test cases
      - `TestListCard.tsx`: Displays list of available tests
      - `TestResultCard.tsx`: Displays the results of the test run
  - `context/`
    - `webSocketContext.tsx`: Provides WebSocket context to the application
  - `hooks/`
    - `useTestRunner.ts`: Main logic for running tests and calculating accuracy
    - `useWebSocket.ts`: Manages WebSocket communication
  - `types/`
    - `Test.ts`: Defines the structure of a test
    - `TestCase.ts`: Defines the structure of a test case
    - `TestResult.ts`: Defines the structure of a test result
    - `Product.ts`: Defines the structure of a product
  - `App.tsx`: Main application component
  - `main.tsx`: Entry point of the application

## Key Components

### useTestRunner Hook

The `useTestRunner` hook is central to the application's functionality. It:

- Manages the state of test execution
- Calculates product and feature accuracy
- Handles test execution in batches
- Provides functions to start, pause, resume, and retry tests

### TestExecutionCard

The `TestExecutionCard` component visualizes the test execution process, displaying:

- Real-time progress
- Pass/fail counts
- Average product and feature accuracy
- Controls for starting, pausing, resuming, and retrying tests

## Accuracy Calculation

The application calculates two types of accuracy:

1. Product Accuracy: Measures the correctness of returned products for each test case.
2. Feature Accuracy: Measures the correctness of extracted features for each product, accounting for "NA" (Not Available) values.

## Configuration

The WebSocket connection URL can be configured in `src/context/webSocketContext.tsx`. Update the `io()` call with the appropriate URL for your backend server.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
