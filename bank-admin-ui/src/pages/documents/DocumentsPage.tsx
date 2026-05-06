import { useRef, useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, RefreshCw, Trash2, FileText } from 'lucide-react'
import { documentsApi, type RagDocument } from '@/api/documents'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { DocStatusBadge } from '@/components/common/StatusBadge'
import { RoleGuard } from '@/components/common/RoleGuard'
import { formatDate } from '@/lib/utils'
import { toast } from '@/components/ui/toaster'

const COLLECTIONS = ['rbi_guidelines', 'bank_policies']

function UploadModal({ replaceDoc, onClose }: { replaceDoc?: RagDocument; onClose: () => void }) {
  const queryClient = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [collection, setCollection] = useState(replaceDoc?.collection_name ?? 'rbi_guidelines')
  const [docName, setDocName] = useState(replaceDoc?.document_name ?? '')
  const [jobId, setJobId] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)

  const mutation = useMutation({
    mutationFn: () => replaceDoc
      ? documentsApi.replace(replaceDoc.id, file!, docName)
      : documentsApi.upload(file!, collection, docName),
    onSuccess: (job) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      setJobId(job.id)
      toast({ title: 'Upload started', description: 'Processing PDF and building embeddings…' })
    },
    onError: (e: any) => toast({ title: 'Upload failed', description: e.response?.data?.detail || String(e), variant: 'destructive' }),
  })

  // Poll job status
  useEffect(() => {
    if (!jobId) return
    const interval = setInterval(async () => {
      try {
        const job = await documentsApi.getJob(jobId)
        setProgress(job.progress_pct)
        if (job.status === 'COMPLETED') {
          clearInterval(interval)
          queryClient.invalidateQueries({ queryKey: ['documents'] })
          toast({ title: 'Ingestion complete', description: `Document is now active in Qdrant.` })
          onClose()
        } else if (job.status === 'FAILED') {
          clearInterval(interval)
          toast({ title: 'Ingestion failed', description: job.error_message ?? 'Unknown error', variant: 'destructive' })
        }
      } catch { clearInterval(interval) }
    }, 3000)
    return () => clearInterval(interval)
  }, [jobId])

  return (
    <DialogContent className="max-w-md">
      <DialogHeader>
        <DialogTitle>{replaceDoc ? 'Replace Document' : 'Upload Document'}</DialogTitle>
      </DialogHeader>
      <div className="space-y-4">
        {!replaceDoc && (
          <div className="space-y-1">
            <Label>Collection</Label>
            <select value={collection} onChange={(e) => setCollection(e.target.value)} className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              {COLLECTIONS.map((c) => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
            </select>
          </div>
        )}
        <div className="space-y-1">
          <Label>Document Name</Label>
          <Input value={docName} onChange={(e) => setDocName(e.target.value)} placeholder="e.g. RBI Guidelines 2024" />
        </div>
        <div className="space-y-1">
          <Label>PDF File</Label>
          <div
            className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 p-6 cursor-pointer hover:border-primary/40"
            onClick={() => fileRef.current?.click()}
          >
            <FileText className="h-8 w-8 text-muted-foreground mb-2" />
            {file ? <p className="text-sm font-medium">{file.name}</p> : <p className="text-sm text-muted-foreground">Click to select PDF</p>}
          </div>
          <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </div>
        {jobId && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Processing…</span><span>{progress}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-gray-100">
              <div className="h-2 rounded-full bg-primary transition-all" style={{ width: `${progress}%` }} />
            </div>
          </div>
        )}
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
        <Button onClick={() => mutation.mutate()} disabled={!file || !docName.trim() || mutation.isPending || !!jobId}>
          {mutation.isPending ? 'Uploading…' : 'Upload'}
        </Button>
      </DialogFooter>
    </DialogContent>
  )
}

export default function DocumentsPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<string>('rbi_guidelines')
  const [uploading, setUploading] = useState(false)
  const [replacing, setReplacing] = useState<RagDocument | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['documents', activeTab],
    queryFn: () => documentsApi.list(activeTab),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['documents'] }); toast({ title: 'Document deleted' }) },
    onError: (e: any) => toast({ title: 'Delete failed', description: e.response?.data?.detail, variant: 'destructive' }),
  })

  return (
    <div className="space-y-4">
      {/* Tabs */}
      <div className="flex gap-2 border-b">
        {COLLECTIONS.map((col) => (
          <button
            key={col}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === col ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-gray-900'}`}
            onClick={() => setActiveTab(col)}
          >
            {col.replace('_', ' ')}
          </button>
        ))}
        <div className="ml-auto pb-2">
          <RoleGuard permission="upload_documents">
            <Button size="sm" onClick={() => setUploading(true)} className="gap-2">
              <Upload className="h-4 w-4" /> Upload Document
            </Button>
          </RoleGuard>
        </div>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-40 text-muted-foreground">Loading…</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Document</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Chunks</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Size</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Uploaded</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.filter(d => d.status !== 'DELETED').map((doc) => (
                  <tr key={doc.id} className="border-b last:border-0">
                    <td className="px-4 py-3">
                      <p className="font-medium">{doc.document_name}</p>
                      <p className="text-xs text-muted-foreground">{doc.original_filename}</p>
                    </td>
                    <td className="px-4 py-3"><DocStatusBadge status={doc.status} /></td>
                    <td className="px-4 py-3 text-right">{doc.chunk_count ?? '—'}</td>
                    <td className="px-4 py-3 text-right text-xs">{doc.file_size_bytes ? `${(doc.file_size_bytes / 1024).toFixed(0)} KB` : '—'}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{formatDate(doc.created_at)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        {doc.status === 'ACTIVE' && (
                          <RoleGuard permission="replace_documents">
                            <Button variant="ghost" size="icon" title="Replace" onClick={() => setReplacing(doc)}>
                              <RefreshCw className="h-3.5 w-3.5" />
                            </Button>
                          </RoleGuard>
                        )}
                        <RoleGuard permission="delete_documents">
                          <Button variant="ghost" size="icon" title="Delete" className="text-destructive hover:text-destructive" onClick={() => deleteMutation.mutate(doc.id)}>
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </RoleGuard>
                      </div>
                    </td>
                  </tr>
                ))}
                {(data?.items.filter(d => d.status !== 'DELETED').length ?? 0) === 0 && (
                  <tr><td colSpan={6} className="px-4 py-12 text-center text-muted-foreground">No documents in this collection</td></tr>
                )}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      <Dialog open={uploading || !!replacing} onOpenChange={(open) => { if (!open) { setUploading(false); setReplacing(null) } }}>
        {(uploading || replacing) && (
          <UploadModal replaceDoc={replacing ?? undefined} onClose={() => { setUploading(false); setReplacing(null) }} />
        )}
      </Dialog>
    </div>
  )
}
