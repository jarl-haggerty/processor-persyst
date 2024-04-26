# Persyst Processor

### Local Development
To run the processor on a specific Persyst file copy the file into a local
`data/input` directory and run the processor using `make`. For example:

```bash
mkdir -p ./data/input # initialize the local data directory and corresponding input sub-directory
cp sample_data/test.lay ./data/input/ # copy an lay file into the local data input directory
cp sample_data/test.dat ./data/input/ # copy an dat file into the local data input directory
make run # run the Persyst processor
```

Output data files will be written to the local `data/output/` directory.

### Output Specification:

**Continuously Sampled Data:**

**The output of the processor should include the following:**
1. A single log (singer or other inspired) of records depicting chunks of data for channels. Each records contains:
   1. Channel Label
   2. Chunk Sampling Rate
   3. Nr. Samples in Chunk
   4. Unit of measurement
   5. Datatype of sample in accompanying binary file (float64, int16,...)
   6. Name of binary file associated with the record.
   7. Time of the first sample in the chunk (in uUTC time)
2. A binary file with continuous data associatd with a single channel of the source file

When there are gaps in the source-file, this will be represented by multiple records for a channel. Records cannot overlap
and the processor should ensure that the timestamp associated with the first sample of a later chunk is larger than 
the timestamp of first record in previous chunk + NrSamples*Sampling_period of previous chunk.


**Unit Data**
Should be something similar
