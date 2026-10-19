"""Apache Beam pipeline: clean health claims data and compute MLR per client.

Steps
  1. Read the CSV and drop exact duplicate rows        (ReadFromText, Distinct)
  2. Parse rows; send bad rows to a separate output    (ParDo + TaggedOutput)
  3. Sum premium and claims per client                 (CombinePerKey + custom CombineFn)
  4. Compute each client's MLR and flag high-risk ones (MapTuple, Filter)
  5. Sum claims per month                              (CombinePerKey(sum))
  6. Build a run summary                               (Count, CombineGlobally, side inputs)
  7. Write every result to outputs/                    (WriteToText)

Runs locally with the DirectRunner:
    python src/pipeline.py --input data/claims.csv --output_dir outputs --threshold 1.0
"""
import argparse

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

from transforms import HEADER, format_client, mlr, parse_row


class ParseRow(beam.DoFn):
    """Valid rows go to the main output, bad rows to the 'invalid' output."""

    def process(self, line):
        if line.strip() == HEADER:
            return
        try:
            yield parse_row(line)
        except ValueError as err:
            yield beam.pvalue.TaggedOutput("invalid", f"{line.strip()},{err}")


class SumPremiumAndClaims(beam.CombineFn):
    """Adds up (premium, claims) and counts how many rows were added."""

    def create_accumulator(self):
        return (0.0, 0.0, 0)

    def add_input(self, acc, value):
        premium, claims = value
        return (acc[0] + premium, acc[1] + claims, acc[2] + 1)

    def merge_accumulators(self, accs):
        accs = list(accs)
        return (
            sum(a[0] for a in accs),
            sum(a[1] for a in accs),
            sum(a[2] for a in accs),
        )

    def extract_output(self, acc):
        return acc


def make_summary(_, valid, invalid, clients, high_risk, totals):
    premium, claims, _rows = totals
    return "\n".join([
        f"valid_rows={valid}",
        f"invalid_rows={invalid}",
        f"clients={clients}",
        f"high_risk_clients={high_risk}",
        f"total_premium={premium:.2f}",
        f"total_claims={claims:.2f}",
        f"overall_mlr={mlr(premium, claims)}",
    ])


def write_csv(pcoll, path, header):
    name = path.rsplit("/", 1)[-1]
    return pcoll | f"Write {name}" >> beam.io.WriteToText(
        path, file_name_suffix=".csv", shard_name_template="", header=header
    )


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/claims.csv")
    parser.add_argument("--output_dir", default="outputs")
    parser.add_argument("--threshold", type=float, default=1.0)
    args, beam_args = parser.parse_known_args(argv)
    out = args.output_dir
    threshold = args.threshold

    with beam.Pipeline(options=PipelineOptions(beam_args)) as p:
        lines = (
            p
            | "Read CSV" >> beam.io.ReadFromText(args.input)
            | "Drop duplicates" >> beam.Distinct()
        )

        parsed = lines | "Parse rows" >> beam.ParDo(ParseRow()).with_outputs(
            "invalid", main="valid"
        )
        valid, invalid = parsed.valid, parsed.invalid

        # Per-client totals and MLR
        client_totals = (
            valid
            | "Key by client" >> beam.Map(
                lambda r: (r["client_id"], (r["premium"], r["claims_paid"])))
            | "Sum per client" >> beam.CombinePerKey(SumPremiumAndClaims())
        )
        high_risk_totals = client_totals | "Keep high MLR" >> beam.Filter(
            lambda kv: mlr(kv[1][0], kv[1][1]) > threshold)

        # Claims per month
        monthly = (
            valid
            | "Key by month" >> beam.Map(lambda r: (r["month"], r["claims_paid"]))
            | "Sum per month" >> beam.CombinePerKey(sum)
            | "Format months" >> beam.MapTuple(lambda m, c: f"{m},{c:.2f}")
        )

        # Run summary, built from single values passed in as side inputs
        overall = (
            valid
            | "Premium and claims" >> beam.Map(lambda r: (r["premium"], r["claims_paid"]))
            | "Sum overall" >> beam.CombineGlobally(SumPremiumAndClaims())
        )
        summary = (
            p
            | "Start summary" >> beam.Create([None])
            | "Build summary" >> beam.Map(
                make_summary,
                valid=beam.pvalue.AsSingleton(
                    valid | "Count valid" >> beam.combiners.Count.Globally()),
                invalid=beam.pvalue.AsSingleton(
                    invalid | "Count invalid" >> beam.combiners.Count.Globally()),
                clients=beam.pvalue.AsSingleton(
                    client_totals | "Count clients" >> beam.combiners.Count.Globally()),
                high_risk=beam.pvalue.AsSingleton(
                    high_risk_totals | "Count high risk" >> beam.combiners.Count.Globally()),
                totals=beam.pvalue.AsSingleton(overall),
            )
        )

        client_header = "client_id,months,total_premium,total_claims,mlr"
        write_csv(client_totals | "Format clients" >> beam.MapTuple(format_client),
                  f"{out}/client_mlr", client_header)
        write_csv(high_risk_totals | "Format high risk" >> beam.MapTuple(format_client),
                  f"{out}/high_risk_clients", client_header)
        write_csv(monthly, f"{out}/monthly_claims", "month,total_claims")
        write_csv(invalid, f"{out}/invalid_rows", HEADER + ",reason")
        summary | "Write summary" >> beam.io.WriteToText(
            f"{out}/summary", file_name_suffix=".txt", shard_name_template="")


if __name__ == "__main__":
    run()
