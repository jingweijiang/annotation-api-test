#!/usr/bin/env groovy

/**
 * Jenkins Pipeline for API Test Automation Framework
 * Enterprise-grade pipeline with parallel execution, quality gates, and comprehensive reporting
 */

pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '30'))
        timeout(time: 2, unit: 'HOURS')
        timestamps()
        ansiColor('xterm')
        parallelsAlwaysFailFast()
    }
    
    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'staging', 'prod'],
            description: 'Target environment for testing'
        )
        choice(
            name: 'TEST_SUITE',
            choices: ['smoke', 'regression', 'full', 'performance', 'security'],
            description: 'Test suite to execute'
        )
        booleanParam(
            name: 'PARALLEL_EXECUTION',
            defaultValue: true,
            description: 'Enable parallel test execution'
        )
        string(
            name: 'PERFORMANCE_THRESHOLD',
            defaultValue: '2000',
            description: 'Performance threshold in milliseconds'
        )
    }
    
    environment {
        PYTHON_VERSION = '3.11'
        PIP_CACHE_DIR = "${WORKSPACE}/.cache/pip"
        PYTEST_CACHE_DIR = "${WORKSPACE}/.cache/pytest"
        ALLURE_RESULTS_DIR = "reports/allure-results"
        ALLURE_REPORT_DIR = "reports/allure-report"
        COVERAGE_REPORT_DIR = "reports/coverage"
        
        // Environment-specific variables
        API_BASE_URL = getApiBaseUrl(params.ENVIRONMENT)
        TEST_AUTH_TOKEN = credentials("api-test-token-${params.ENVIRONMENT}")
        SLACK_WEBHOOK = credentials('slack-webhook-api-tests')
    }
    
    stages {
        stage('Preparation') {
            steps {
                script {
                    echo "Starting API Test Pipeline"
                    echo "Environment: ${params.ENVIRONMENT}"
                    echo "Test Suite: ${params.TEST_SUITE}"
                    echo "Parallel Execution: ${params.PARALLEL_EXECUTION}"
                    
                    // Clean workspace
                    cleanWs()
                    
                    // Checkout code
                    checkout scm
                    
                    // Setup Python environment
                    sh '''
                        python3 --version
                        python3 -m venv venv
                        source venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install -r requirements-dev.txt
                        pip install -e .
                    '''
                }
            }
        }
        
        stage('Code Quality') {
            parallel {
                stage('Linting') {
                    steps {
                        sh '''
                            source venv/bin/activate
                            black --check --diff framework/ tests/ || exit 1
                            isort --check-only --diff framework/ tests/ || exit 1
                            flake8 framework/ tests/ --output-file=reports/flake8-report.txt || exit 1
                        '''
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'reports/flake8-report.txt', allowEmptyArchive: true
                        }
                    }
                }
                
                stage('Type Checking') {
                    steps {
                        sh '''
                            source venv/bin/activate
                            mypy framework/ --html-report reports/mypy || exit 1
                        '''
                    }
                    post {
                        always {
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'reports/mypy',
                                reportFiles: 'index.html',
                                reportName: 'MyPy Type Check Report'
                            ])
                        }
                    }
                }
                
                stage('Security Scan') {
                    steps {
                        sh '''
                            source venv/bin/activate
                            bandit -r framework/ -f json -o reports/bandit-report.json || true
                            safety check --json --output reports/safety-report.json || true
                        '''
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'reports/*-report.json', allowEmptyArchive: true
                        }
                    }
                }
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh '''
                    source venv/bin/activate
                    pytest tests/unit/ \
                        --junitxml=reports/junit/unit-tests.xml \
                        --cov=framework \
                        --cov-report=xml:reports/coverage/unit-coverage.xml \
                        --cov-report=html:reports/coverage/unit-html \
                        --alluredir=${ALLURE_RESULTS_DIR}/unit
                '''
            }
            post {
                always {
                    junit 'reports/junit/unit-tests.xml'
                    publishCoverage adapters: [
                        coberturaAdapter('reports/coverage/unit-coverage.xml')
                    ], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                    
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'reports/coverage/unit-html',
                        reportFiles: 'index.html',
                        reportName: 'Unit Test Coverage Report'
                    ])
                }
            }
        }
        
        stage('API Tests') {
            parallel {
                stage('Smoke Tests') {
                    when {
                        anyOf {
                            expression { params.TEST_SUITE == 'smoke' }
                            expression { params.TEST_SUITE == 'full' }
                        }
                    }
                    steps {
                        sh '''
                            source venv/bin/activate
                            pytest tests/api/ \
                                -m "smoke" \
                                --env=${ENVIRONMENT} \
                                --junitxml=reports/junit/smoke-tests.xml \
                                --alluredir=${ALLURE_RESULTS_DIR}/smoke \
                                --maxfail=3
                        '''
                    }
                    post {
                        always {
                            junit 'reports/junit/smoke-tests.xml'
                        }
                    }
                }
                
                stage('Regression Tests') {
                    when {
                        anyOf {
                            expression { params.TEST_SUITE == 'regression' }
                            expression { params.TEST_SUITE == 'full' }
                        }
                    }
                    steps {
                        script {
                            def parallelFlag = params.PARALLEL_EXECUTION ? '-n auto' : ''
                            sh """
                                source venv/bin/activate
                                pytest tests/api/ \
                                    -m "regression" \
                                    --env=${params.ENVIRONMENT} \
                                    --junitxml=reports/junit/regression-tests.xml \
                                    --alluredir=${ALLURE_RESULTS_DIR}/regression \
                                    ${parallelFlag}
                            """
                        }
                    }
                    post {
                        always {
                            junit 'reports/junit/regression-tests.xml'
                        }
                    }
                }
                
                stage('Integration Tests') {
                    when {
                        anyOf {
                            expression { params.TEST_SUITE == 'full' }
                            expression { params.ENVIRONMENT != 'prod' }
                        }
                    }
                    steps {
                        sh '''
                            source venv/bin/activate
                            pytest tests/integration/ \
                                --env=${ENVIRONMENT} \
                                --junitxml=reports/junit/integration-tests.xml \
                                --alluredir=${ALLURE_RESULTS_DIR}/integration
                        '''
                    }
                    post {
                        always {
                            junit 'reports/junit/integration-tests.xml'
                        }
                    }
                }
                
                stage('Contract Tests') {
                    when {
                        anyOf {
                            expression { params.TEST_SUITE == 'full' }
                            expression { params.ENVIRONMENT != 'prod' }
                        }
                    }
                    steps {
                        sh '''
                            source venv/bin/activate
                            pytest tests/contract/ \
                                --junitxml=reports/junit/contract-tests.xml \
                                --alluredir=${ALLURE_RESULTS_DIR}/contract
                        '''
                    }
                    post {
                        always {
                            junit 'reports/junit/contract-tests.xml'
                            archiveArtifacts artifacts: 'tests/contract/pacts/**/*.json', allowEmptyArchive: true
                        }
                    }
                }
            }
        }
        
        stage('Performance Tests') {
            when {
                anyOf {
                    expression { params.TEST_SUITE == 'performance' }
                    expression { params.TEST_SUITE == 'full' }
                }
            }
            steps {
                sh '''
                    source venv/bin/activate
                    pytest tests/performance/ \
                        --env=${ENVIRONMENT} \
                        --junitxml=reports/junit/performance-tests.xml \
                        --alluredir=${ALLURE_RESULTS_DIR}/performance \
                        --performance-threshold=${PERFORMANCE_THRESHOLD}
                '''
            }
            post {
                always {
                    junit 'reports/junit/performance-tests.xml'
                }
            }
        }
        
        stage('Security Tests') {
            when {
                anyOf {
                    expression { params.TEST_SUITE == 'security' }
                    expression { params.TEST_SUITE == 'full' }
                }
            }
            steps {
                sh '''
                    source venv/bin/activate
                    pytest tests/security/ \
                        --env=${ENVIRONMENT} \
                        --junitxml=reports/junit/security-tests.xml \
                        --alluredir=${ALLURE_RESULTS_DIR}/security
                '''
            }
            post {
                always {
                    junit 'reports/junit/security-tests.xml'
                }
            }
        }
        
        stage('Generate Reports') {
            steps {
                script {
                    // Generate Allure report
                    allure([
                        includeProperties: false,
                        jdk: '',
                        properties: [],
                        reportBuildPolicy: 'ALWAYS',
                        results: [[path: env.ALLURE_RESULTS_DIR]]
                    ])
                    
                    // Archive test artifacts
                    archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
                    
                    // Publish test results summary
                    publishTestResults testResultsPattern: 'reports/junit/*.xml'
                }
            }
        }
        
        stage('Quality Gates') {
            steps {
                script {
                    // Check test results and coverage
                    def testResults = junit testResults: 'reports/junit/*.xml'
                    def failedTests = testResults.getFailCount()
                    def totalTests = testResults.getTotalCount()
                    def successRate = ((totalTests - failedTests) / totalTests) * 100
                    
                    echo "Test Results: ${totalTests} total, ${failedTests} failed"
                    echo "Success Rate: ${successRate}%"
                    
                    // Quality gate thresholds
                    def minSuccessRate = params.ENVIRONMENT == 'prod' ? 100 : 95
                    def maxFailedTests = params.ENVIRONMENT == 'prod' ? 0 : 5
                    
                    if (successRate < minSuccessRate) {
                        error("Quality gate failed: Success rate ${successRate}% below threshold ${minSuccessRate}%")
                    }
                    
                    if (failedTests > maxFailedTests) {
                        error("Quality gate failed: ${failedTests} failed tests exceeds threshold ${maxFailedTests}")
                    }
                    
                    echo "✅ Quality gates passed"
                }
            }
        }
    }
    
    post {
        always {
            // Clean up
            sh 'rm -rf venv'
            
            // Archive logs
            archiveArtifacts artifacts: 'logs/**/*.log', allowEmptyArchive: true
        }
        
        success {
            script {
                def message = """
                ✅ API Tests Passed
                Environment: ${params.ENVIRONMENT}
                Test Suite: ${params.TEST_SUITE}
                Build: ${env.BUILD_NUMBER}
                Duration: ${currentBuild.durationString}
                """
                
                slackSend(
                    channel: '#api-tests',
                    color: 'good',
                    message: message,
                    teamDomain: 'company',
                    token: env.SLACK_WEBHOOK
                )
            }
        }
        
        failure {
            script {
                def message = """
                ❌ API Tests Failed
                Environment: ${params.ENVIRONMENT}
                Test Suite: ${params.TEST_SUITE}
                Build: ${env.BUILD_NUMBER}
                Build URL: ${env.BUILD_URL}
                """
                
                slackSend(
                    channel: '#api-tests',
                    color: 'danger',
                    message: message,
                    teamDomain: 'company',
                    token: env.SLACK_WEBHOOK
                )
            }
        }
        
        unstable {
            script {
                def message = """
                ⚠️ API Tests Unstable
                Environment: ${params.ENVIRONMENT}
                Test Suite: ${params.TEST_SUITE}
                Build: ${env.BUILD_NUMBER}
                Some tests failed but build continued
                """
                
                slackSend(
                    channel: '#api-tests',
                    color: 'warning',
                    message: message,
                    teamDomain: 'company',
                    token: env.SLACK_WEBHOOK
                )
            }
        }
    }
}

// Helper functions
def getApiBaseUrl(environment) {
    switch(environment) {
        case 'dev':
            return 'https://api-dev.company.com'
        case 'staging':
            return 'https://api-staging.company.com'
        case 'prod':
            return 'https://api.company.com'
        default:
            return 'https://api-dev.company.com'
    }
}
