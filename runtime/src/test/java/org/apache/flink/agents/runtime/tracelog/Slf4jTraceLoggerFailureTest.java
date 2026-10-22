/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.flink.agents.runtime.tracelog;

import org.apache.flink.agents.api.InputEvent;
import org.apache.flink.agents.api.logger.LoggerType;
import org.apache.flink.agents.api.logger.TraceLoggerConfig;
import org.apache.flink.agents.api.trace.TraceContext;
import org.apache.flink.agents.api.trace.TraceRecord;
import org.apache.flink.agents.runtime.metrics.BuiltInMetrics;
import org.apache.flink.api.common.JobID;
import org.apache.flink.api.common.JobInfo;
import org.apache.flink.api.common.TaskInfo;
import org.apache.flink.metrics.SimpleCounter;
import org.apache.flink.streaming.api.operators.StreamingRuntimeContext;
import org.apache.logging.log4j.Level;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.core.Appender;
import org.apache.logging.log4j.core.LogEvent;
import org.apache.logging.log4j.core.LoggerContext;
import org.apache.logging.log4j.core.appender.AbstractAppender;
import org.apache.logging.log4j.core.appender.FileAppender;
import org.apache.logging.log4j.core.appender.OutputStreamManager;
import org.apache.logging.log4j.core.config.Configuration;
import org.apache.logging.log4j.core.config.LoggerConfig;
import org.apache.logging.log4j.core.layout.PatternLayout;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.FilterOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/** Exercises write failures through the automatically configured Log4j2 file appender. */
class Slf4jTraceLoggerFailureTest {

    @TempDir private Path tempDir;

    @Test
    void fileWriteFailuresAreCountedWithoutEscapingAndWarnOnlyOnce() throws Exception {
        LoggerContext context = (LoggerContext) LogManager.getContext(false);
        Configuration configuration = context.getConfiguration();
        String traceName = Slf4jTraceLogger.TRACE_LOGGER_NAME;
        String writerName = TraceLogWriter.class.getName();
        String appenderName = "FlinkAgentsTraceLogAppender";
        LoggerConfig previousTrace = configuration.getLoggers().get(traceName);
        LoggerConfig previousWriter = configuration.getLoggers().get(writerName);
        Appender previousAppender = configuration.getAppender(appenderName);
        String previousLogFile = System.getProperty("log.file");
        List<LogEvent> diagnostics = new ArrayList<>();
        AbstractAppender diagnosticAppender =
                new AbstractAppender(
                        "TraceWriteFailureDiagnostics",
                        null,
                        PatternLayout.createDefaultLayout(),
                        true,
                        null) {
                    @Override
                    public void append(LogEvent event) {
                        diagnostics.add(event.toImmutable());
                    }
                };
        FileAppender fileAppender = null;
        try {
            // Remove a prior test's logger so open() takes the production auto-configuration path.
            configuration.removeLogger(traceName);
            configuration.removeLogger(writerName);
            configuration.getAppenders().remove(appenderName);
            diagnosticAppender.start();
            LoggerConfig writerConfig = new LoggerConfig(writerName, Level.DEBUG, false);
            writerConfig.addAppender(diagnosticAppender, Level.DEBUG, null);
            configuration.addLogger(writerName, writerConfig);
            context.updateLoggers();
            Path logFile = tempDir.resolve("taskmanager.log");
            System.setProperty("log.file", logFile.toString());

            StreamingRuntimeContext runtime = mock(StreamingRuntimeContext.class);
            JobInfo job = mock(JobInfo.class);
            TaskInfo task = mock(TaskInfo.class);
            when(runtime.getJobInfo()).thenReturn(job);
            when(runtime.getTaskInfo()).thenReturn(task);
            when(job.getJobId()).thenReturn(JobID.generate());
            when(task.getTaskName()).thenReturn("agent");
            BuiltInMetrics metrics = mock(BuiltInMetrics.class);
            SimpleCounter failures = new SimpleCounter();
            when(metrics.getTraceLogWriteFailuresCounter()).thenReturn(failures);
            when(metrics.getTraceLogTruncatedRecordsCounter()).thenReturn(new SimpleCounter());
            try (TraceLogWriter writer =
                    TraceLogWriter.forTraceLogger(
                            new Slf4jTraceLogger(
                                    TraceLoggerConfig.builder()
                                            .loggerType(LoggerType.SLF4J)
                                            .build()))) {
                writer.open(runtime, metrics);
                fileAppender = (FileAppender) configuration.getAppender(appenderName);
                assertThat(fileAppender).isNotNull();
                writer.appendAndFlush(inputRecord("before-failure"));
                assertThat(failures.getCount()).isZero();
                Path traceFile = Path.of(logFile + ".trace-log.log");
                assertThat(Files.readString(traceFile)).contains("before-failure");

                // Replace only the destination stream; retain the real logger/appender error path.
                OutputStreamManager manager = fileAppender.getManager();
                Method getStream = OutputStreamManager.class.getDeclaredMethod("getOutputStream");
                getStream.setAccessible(true);
                FailingOutputStream stream =
                        new FailingOutputStream((OutputStream) getStream.invoke(manager));
                Method setStream =
                        OutputStreamManager.class.getDeclaredMethod(
                                "setOutputStream", OutputStream.class);
                setStream.setAccessible(true);
                setStream.invoke(manager, stream);
                stream.failWrites = true;
                for (int attempt = 1; attempt <= 2; attempt++) {
                    assertThatCode(() -> writer.appendAndFlush(inputRecord("failed-write")))
                            .doesNotThrowAnyException();
                    assertThat(failures.getCount()).isEqualTo(attempt);
                }
                assertThat(diagnostics)
                        .filteredOn(
                                event ->
                                        event.getMessage()
                                                .getFormattedMessage()
                                                .startsWith("Trace Log write failed"))
                        .extracting(LogEvent::getLevel)
                        .containsExactly(Level.WARN, Level.DEBUG);
                assertThat(fileAppender.ignoreExceptions()).isFalse();

                stream.failWrites = false;
                writer.appendAndFlush(inputRecord("after-recovery"));
                assertThat(failures.getCount()).isEqualTo(2);
                assertThat(Files.readString(traceFile)).contains("after-recovery");
            }
        } finally {
            configuration.removeLogger(traceName);
            configuration.removeLogger(writerName);
            if (previousTrace != null) {
                configuration.addLogger(traceName, previousTrace);
            }
            if (previousWriter != null) {
                configuration.addLogger(writerName, previousWriter);
            }
            configuration.getAppenders().remove(appenderName);
            if (previousAppender != null) {
                configuration.addAppender(previousAppender);
            }
            context.updateLoggers();
            if (fileAppender != null) {
                fileAppender.stop();
            }
            diagnosticAppender.stop();
            if (previousLogFile == null) {
                System.clearProperty("log.file");
            } else {
                System.setProperty("log.file", previousLogFile);
            }
        }
    }

    private static TraceRecord inputRecord(String value) {
        InputEvent event = new InputEvent(value);
        return TraceRecord.create(
                TraceContext.forEvent(null, event.getType(), event.getId().toString(), null, null),
                null,
                null,
                event.getAttributes());
    }

    private static class FailingOutputStream extends FilterOutputStream {
        private boolean failWrites;

        private FailingOutputStream(OutputStream delegate) {
            super(delegate);
        }

        @Override
        public void write(int value) throws IOException {
            if (failWrites) {
                throw new IOException("Simulated Trace Log disk write failure");
            }
            out.write(value);
        }

        @Override
        public void write(byte[] bytes, int offset, int length) throws IOException {
            if (failWrites) {
                throw new IOException("Simulated Trace Log disk write failure");
            }
            out.write(bytes, offset, length);
        }
    }
}
